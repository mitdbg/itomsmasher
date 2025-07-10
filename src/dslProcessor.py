from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram

import time, os, base64
import re
from typing import Optional, List, Tuple, Any
from markdown import markdown
from playwright.sync_api import sync_playwright

# ProgramExecutor is a class that executes a program of any kind
class ProgramExecutor:
    def __init__(self, programDirectory: ProgramDirectory):
        self.programDirectory = programDirectory
        self.availableDSLProcessors = {
            "basic": BasicDSLProcessor(programDirectory),
            "aiimage": AIImageProcessor(programDirectory)
        }

    def executeProgram(self, programName: str, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        program = self.programDirectory.getProgram(programName)
        if program.dslId not in self.availableDSLProcessors:
            raise ValueError(f"DSL processor {program.dslId} not found")

        dslProcessor = self.availableDSLProcessors[program.dslId]
        return dslProcessor.runProgram(program, input, preferredVisualReturnType)

# DSLProcessor is a generic superclass for all DSL processors
class DSLProcessor:
    def __init__(self):
        pass

    def getVisualReturnTypes(self) -> List[str]:
        pass

    def process(self, program: NamedProgram, input: dict, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        pass

    def __convertToLocalDSL__(self, data: Any) -> str:
        pass

    def __preprocess__(self, code: str, input: dict, preferredVisualType: Optional[str] = None, startBlock: Optional[str] = "{{", endBlock: Optional[str] = "}}") -> str:
        # Any part of the code in double-braces should be replaced with a pre-processed version of the code
        # Let's start by iterating through the code and finding all double-brace blocks
        # We'll replace each double-brace block with the pre-processed version of the code
        # We'll return the pre-processed code

        # initialize variables with contents of input (but make a copy)
        variables = input.copy()
        def processElement(code_block: str, variables: dict) -> Any:
            # Check if the code block is a variable assignment of the form varname = value. Use regex to match this.
            if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]* = .*$", code_block):
                # It's a variable assignment
                # Split the code block into lhs and rhs
                lhs, rhs = code_block.split("=")
                lhs = lhs.strip()
                rhs = rhs.strip()

                rhsProcessed = processElement(rhs, variables)
                variables[lhs] = rhsProcessed
                return None
            
            # Check if the code block is a variable access of the form varname.fieldname. There must be a dot separator. Use regex to match this.
            elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$", code_block):
                # It's a variable access
                varName = code_block.split(".")[0]
                field = code_block.split(".")[1]
                return variables[varName][field]

            # Check if the code block is of the form {{include("programName", input0, input1, input2)}}, where we might have zero or more 'input' parameters.
            # Use a regex to match this.
            elif re.match(r'include\(\s*"([^"]+)"\s*(?:,\s*([^)]+))?\)', code_block):
                # It's an include statement
                # Form of include is 'include("programName", input)'
                match = re.match(r'include\(\s*"([^"]+)"\s*(?:,\s*([^)]+))?\)', code_block)
                programName = match.group(1)
                paramList = match.group(2)
                if paramList is None:
                    paramList = []
                else:
                    paramList = paramList.split(",")
                # strip whitespace from all params
                paramList = [p.strip() for p in paramList]
                includedProgramName = programName.strip("\"'")
                params = [processElement(p, variables) for p in paramList]

                # print all the programs in the program directory
                includedProgram = self.programDirectory.getProgram(includedProgramName)
                providedInputs = {}
                if len(includedProgram.inputs) != len(params):
                    raise ValueError(f"Expected {len(includedProgram.inputs)} parameters for program {includedProgramName}, but got {len(params)} {params}")

                for i in range(len(includedProgram.inputs)):
                    label = includedProgram.inputs[i]
                    param = params[i] if i < len(params) else None
                    providedInputs[label] = param
                inputData = {"startTimestamp": time.time(), "inputs": providedInputs}

                return ProgramExecutor(self.programDirectory).executeProgram(includedProgramName, inputData, preferredVisualType)
            else:
                # It's a value. Either a variable name or a literal value.
                if code_block in variables:
                    return variables[code_block]
                else:
                    # It's a literal value. Parse like a Python atomic literal
                    return eval(code_block)

        def __preprocessBlock__(code_block: str) -> str:
            # If the code block starts with "include", we need to preprocess the include and replace it with the included program's output
            # If the code block has an equals sign, we need to preprocess the variable assignment and replace it with nothing
            # If the code block is a standalone variable, we need to replace it with the variable's value
            return self.__convertToLocalDSL__(processElement(code_block, variables))

        while startBlock in code:
            start = code.find(startBlock)
            end = code.find(endBlock)
            if start == -1 or end == -1:
                break
            # Get the code between the double-braces
            code_block = code[start+2:end]
            # Replace the double-brace block with the pre-processed version of the code
            code = code[:start] + __preprocessBlock__(code_block) + code[end+2:]

        return code


    def runProgram(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = program.codeVersions[-1]
        latestExecutionHistory = program.executions[-1]
        programOutput = self.process(latestCode, input["inputs"], preferredVisualReturnType)
        latestExecutionHistory.append((input, programOutput))
        return programOutput


class AIImageProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["png"]

    def __convertToLocalDSL__(self, data: Any) -> str:
        if data is None:
            return ""
        elif isinstance(data, str):
            return data
        else:
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")

    def process(self, code: str, input: dict, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        # Contact ChatGPT to generate an image based on the text in the code
        # Return the image as a ProgramOutput

        # Preprocess the code so that all variables are replaced with their values
        code = self.__preprocess__(code, input, preferredVisualReturnType)

        import requests

        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Call OpenAI API to generate image
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "prompt": code,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")

        # Get base64 encoded image and convert to bytes
        image_data = response.json()["data"][0]["b64_json"]
        png_bytes = base64.b64decode(image_data)
        return ProgramOutput(time.time(), "png", png_bytes, {})

# BasicDSLProcessor is a DSL processor for the basic DSL
class BasicDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html"]
    
    def __convertToLocalDSL__(self, data: Any) -> str:
        if data is None:
            return ""
        elif isinstance(data, str):
            return data
        elif isinstance(data, int):
            return str(data)
        elif isinstance(data, float):
            return str(data)
        elif isinstance(data, ProgramOutput):            
            # The returned item is an example of ProgramOutput
            if data.visualReturnType() == "html":
                return data.viz()
            elif data.visualReturnType() == "png":
                # Be sure to base64 encode the png
                return f"![{data.visualReturnType()}](data:image/png;base64,{base64.b64encode(data.viz()).decode('utf-8')})"
            else:
                # We can only convert these two visual return types to markdown
                raise ValueError(f"Invalid visual return type: {data.visualReturnType()}")
        elif isinstance(data, dict):
            #It's not a ProgramOutput. It's just a dictionary, so convert to a string representation
            return "\n".join([f"{key}: {value}" for key, value in data.items()])
        elif isinstance(data, list):
            return "\n".join([self.__convertToLocalDSL__(item) for item in data])
        else:
            # What else could it be?
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")

    def process(self, code: str, input: dict, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

        # Preprocess the document
        finalizedMarkdown = self.__preprocess__(code, input, preferredVisualReturnType)
        html = markdown(finalizedMarkdown)

        if preferredVisualReturnType == "html":
            return ProgramOutput(endTimestamp=time.time(),
                                 visualReturnType="html",
                                 visualOutput=html,
                                 dataOutputs={})
        
        elif preferredVisualReturnType == "png":
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html)
                png_bytes = page.screenshot(full_page=True, type="png")
                browser.close()
                return ProgramOutput(endTimestamp=time.time(),
                                     visualReturnType="png",
                                     visualOutput=png_bytes,
                                     dataOutputs={})
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")






