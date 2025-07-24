from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
from dslProcessor import DSLProcessor, BasicDSLProcessor
from aiImageDslProcessor import AIImageProcessor
from spreadsheetDslProcessor import SpreadsheetDSLProcessor
from VegaDSLProcessor import VegaDSLProcessor
from JavascriptDSLProcessor import JavascriptDSLProcessor
from PlaceHolderDSLProcessor import PlaceHolderDSLProcessor
from SlideVideoDSLProcessor import SlideVideoDSLProcessor
from SlideDSLProcessor import SlideDSLProcessor
from PythonDSLProcessor import PythonDSLProcessor
from typing import Optional
import requests
import json
import os

# ProgramExecutor is a class that executes a program of any kind
class ProgramExecutor:
    def __init__(self, programDirectory: ProgramDirectory):
        self.programDirectory = programDirectory
        self.availableDSLProcessors = {
            "aiimage": AIImageProcessor(programDirectory),
            "spreadsheet": SpreadsheetDSLProcessor(programDirectory),
            "vega-lite": VegaDSLProcessor(programDirectory),
            #"javascript": JavascriptDSLProcessor(programDirectory),
            "basic": BasicDSLProcessor(programDirectory),
            "slidevideo": SlideVideoDSLProcessor(programDirectory),
            "slides": SlideDSLProcessor(programDirectory),
            "placeholder": PlaceHolderDSLProcessor(programDirectory),
            "python": PythonDSLProcessor(programDirectory)
        }
        self.programDirectory.setProgramExecutor(self)

    def getVisualReturnTypesForProgram(self, program: NamedProgram) -> list[str]:
        dslProcessor = self.availableDSLProcessors[program.dslId]
        return dslProcessor.getVisualReturnTypes()

    def executeProgram(self, programName: str, input: ProgramInput, preferredVisualReturnType: Optional[str] = None, inferInputs: bool = False, callingProgramContext: Optional[str] = None,config: Optional[dict] = None) -> ProgramOutput:
        program = self.programDirectory.getProgram(programName)
        if program.dslId not in self.availableDSLProcessors:
            raise ValueError(f"DSL processor {program.dslId} not found")

        aiInputs = False
        if aiInputs:
            # Check to see if all of the inputs are present in the input dictionary
            neededInputs = []
            for inputName in program.inputs:
                if inputName not in input["inputs"]:
                    if not inferInputs:
                        raise ValueError(f"Input {inputName} not found in input dictionary")
                    else:
                        print(f"Input {inputName} not found in input dictionary, but inferring inputs is allowed")
                        neededInputs.append(inputName)

            if len(neededInputs) > 0:
                programDescription = program.description
                neededInputList = "\n".join(neededInputs)
                prompt = f"""
                You are a helpful assistant that can infer the inputs for a program.
                The program is called {programName}, and its description is {programDescription}.
                The inputs are {neededInputList}.
                The context of the calling program is {callingProgramContext}.
                Please return a set of key/value pairs for the inputs that are needed.
                Return this in the form of a JSON object with the keys and values.
                If you cannot infer a good value for an input, make as good as guess as possible. Do not leave any inputs blank.
                """ 
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
                    json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0, "max_tokens": 1000}
                )
                extractedJsonStr = response.json()["choices"][0]["message"]["content"]
                # If the json string starts with 'json' or 'JSON', remove it
                # Strip any series of single or doublequotes from the beginning and end
                while extractedJsonStr.startswith('"') or extractedJsonStr.startswith("'") or extractedJsonStr.startswith("`"):
                    extractedJsonStr = extractedJsonStr[1:]
                while extractedJsonStr.endswith('"') or extractedJsonStr.endswith("'") or extractedJsonStr.endswith("`"):
                    extractedJsonStr = extractedJsonStr[:-1]
                if extractedJsonStr.startswith("json") or extractedJsonStr.startswith("JSON"):
                    extractedJsonStr = extractedJsonStr[len("json"):].strip()
                extractedJsonStr = extractedJsonStr.strip()

                try:
                    extractedJson = json.loads(extractedJsonStr)
                    for k in neededInputs:
                        if k not in extractedJson:
                            raise ValueError(f"Input {k} not found in input dictionary")
                        input["inputs"][k] = extractedJson[k]
                except Exception as e:
                    print("Error parsing JSON: ", e)
                    pass

        dslProcessor = self.availableDSLProcessors[program.dslId]
        return dslProcessor.runProgram(program, input, preferredVisualReturnType)

