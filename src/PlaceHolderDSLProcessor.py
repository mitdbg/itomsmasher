from openai import OpenAI
import cv2
import hashlib
import os
from pydub import AudioSegment
import uuid
from dslProcessor import DSLProcessor, BasicDSLProcessor
from programs import ProgramOutput, ProgramDirectory, ProgramInput
from typing import List, Any
import os
import time
import shutil
from dotenv import dotenv_values
import pkg_resources

class PlaceHolderDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory
    
    def getVisualReturnTypes(self) -> List[str]:
        return ["html","md"]
    
    def getInstalledPackages(self) -> List[str]:
        installed_packages = pkg_resources.working_set
        installed = []
        for i in installed_packages:
            installed.append(f"{i.key}")
        return installed
    
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str,config:dict) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        
        if os.path.exists(".env"):
            env = dotenv_values(".env")
            client = OpenAI(api_key=env["OPENAI_API_KEY"])
        else:
            client = OpenAI()

        itomidstring = ""
        innerInput = {}
        forceRefresh = False
        for key, value in sorted(input.items()):
            if key != "_forceRefresh":
                itomidstring += f"{key}: {value}\n"
            # if the key doesn't start with _, add it to the innerInput
            if not key.startswith("_"):
                innerInput[key] = value
            if key == "_forceRefresh":
                forceRefresh = value
        for key, value in sorted(config.items()):
            itomidstring += f"{key}: {value}\n"
        for key in sorted(outputNames):
            itomidstring += f"{key}\n"
        
        #print(itomidstring)
        itomhash = hashlib.md5(itomidstring.encode()).hexdigest()

        # if the .genitomcache directory doesn't exist, create it
        if not os.path.exists(".genitomcache"):
            os.makedirs(".genitomcache")

        if not forceRefresh:
            try:
                program = self.programDirectory.getProgram(f"itom_{itomhash}")
                # Load and refresh the program directory
                programExecutor = self.programDirectory.getProgramExecutor()
                programOutput = programExecutor.executeProgram(program.name, ProgramInput(startTimestamp=0, inputs=innerInput), preferredVisualReturnType=preferredVisualReturnType, config={})
                return programOutput
            except Exception as e:
                #print(e)
                print("Program doesn't exist, attempting to create it ", e)
        else:
            print("Force refreshing generated itom")

        context = input['_context']
        outputNames = input['_outputs']
        
        function_name = "itom_"+itomhash[:8]

        prompt = f"""
Complete the python function based on the spec: {context}

The function should return a dictionary with the following keys:
{outputNames}

It will accept the following inputs: {innerInput.keys()}

The function should not call any network functions or modify any files. 
If you need to make up data, use a random generator that outputs reasonable values 
given the context. Try to use the most realistic data possible (e.g., don't just use
random words if something specific is asked for)

Only return the code completion! No other text. It is important that all imports
and sub-functions are *inside* the function.

The following packages are installed and can be used:
{self.getInstalledPackages()}

Do not use any other libraries that would require installation. 
Again, any imports or sub-functions should be *inside* the function.

Make a plan for the program and then write the rest of the program to complete the function:
        """

        docstring = "\t\"\"\"Function for: " + context + "\n"
        signature = f"def {function_name}("
        args = []
        if (len(innerInput) > 0):
            docstring += "\tArguments:\n"
            for key in innerInput.keys():
                args.append(f"{key}=None")
                docstring += f"\t\t{key}, example: {innerInput[key]}\n"
        signature += ", ".join(args)
        signature += "):"

        if (len(outputNames) > 0):
            docstring += "\tReturns:\n\t\t{\n"
            for key in outputNames:
                docstring += f"\t\t '{key}': ...,\n"
            docstring += "\t\t}\n"

        docstring += "\t\"\"\""

        prompt += f"""
{signature}
{docstring}

"""
        
#        print(prompt)

        #print(signature)
        #print(prompt)
        messages = [
                {"role": "system", "content": "You are a helpful assistant that can generate code."},
                {"role": "user", "content": prompt}
            ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        response_text = response.choices[0].message.content


        response_text = response_text.split("```python")[1].split("```")[0]

        # let's test the code
        try:
            exec(response_text)
            exec(f"{function_name}()")
            print("Code executed successfully")
        except Exception as e:
            print(e)
            print("Code failed to execute, attempting to fix it")
            messages.append({"role": "assistant", "content": response_text})
            newprompt = f"""
The code failed to execute with the following error:
{e}

Please fix the code so that it executes successfully. 
Remember, all imports and sub-functions should be *inside* the function.

Reason about the error and return the corrected code.
"""
            messages.append({"role": "user", "content": newprompt})
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            response_text = response.choices[0].message.content
            response_text = response_text.split("```python")[1].split("```")[0]
            #print(response_text)

        itom = f"""#@ dsl: python
#@ config: mainfunc='{function_name}'
"""

        for key in outputNames:
            itom += f"#@ output: {key}\n"

        itom += response_text

        # save the file to .genitomcache/itom_<hash>.itom
        with open(f".genitomcache/itom_{itomhash}.itom", "w") as file:
            file.write(itom)

        self.programDirectory.addNewProgram(f"itom_{itomhash}", f"Generated from {context}", itom, refresh=True)

        try:
            program = self.programDirectory.getProgram(f"itom_{itomhash}")
            # Load and refresh the program directory
            programExecutor = self.programDirectory.getProgramExecutor()
            programOutput = programExecutor.executeProgram(program.name, ProgramInput(startTimestamp=0, inputs=innerInput), preferredVisualReturnType=preferredVisualReturnType, config={})
            return programOutput
        except Exception as e:
            print(e)
            raise e


