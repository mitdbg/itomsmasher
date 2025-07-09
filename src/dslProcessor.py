from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram

import time
from typing import Optional, List, Tuple, Any
import base64
from markdown import markdown
from playwright.sync_api import sync_playwright

# ProgramExecutor is a class that executes a program of any kind
class ProgramExecutor:
    def __init__(self, programDirectory: ProgramDirectory):
        self.programDirectory = programDirectory
        self.availableDSLProcessors = {
            "basic": BasicDSLProcessor(programDirectory)
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

    def process(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        pass

    def runProgram(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = program.codeVersions[-1]
        latestExecutionHistory = program.executions[-1]
        programOutput = self.process(latestCode, input, preferredVisualReturnType)
        latestExecutionHistory.append((input, programOutput))
        return programOutput

# BasicDSLProcessor is a DSL processor for the basic DSL
class BasicDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html"]

    def __preprocess__(self, code: str, preferredVisualType: Optional[str] = None) -> str:
        # Any part of the code in double-braces should be replaced with a pre-processed version of the code
        # Let's start by iterating through the code and finding all double-brace blocks
        # We'll replace each double-brace block with the pre-processed version of the code
        # We'll return the pre-processed code

        variables = {}
        def processElement(code_block: str, variables: dict) -> Any:
            if "=" in code_block:
                lhs = code_block.split("=")[0].strip()
                rhs = code_block.split("=")[1].strip()

                rhsProcessed = processElement(rhs, variables)
                variables[lhs] = rhsProcessed
                return None
            elif code_block.startswith("include"):
                # Invoke the include program
                # Form of include is 'include("programName", input)'
                paramList = code_block.split("(")[1].split(")")[0].split(",")
                # strip whitespace from all params
                paramList = [p.strip() for p in paramList]

                includedProgramName = paramList[0].strip("\"'")
                paramList = paramList[1:]
                # strip the end-parenthesis
                params = []
                for p in paramList:
                    # It's a list of names
                    paramString = p.strip()
                    params.append(processElement(paramString, variables))

                # WARNING: we drop the parameters currently!!!!! They are not passed-in!
                # print all the programs in the program directory
                includedProgram = self.programDirectory.getProgram(includedProgramName)
                providedInputs = {}
                if len(includedProgram.inputs) != len(params):
                    raise ValueError(f"Expected {len(includedProgram.inputs)} parameters for program {includedProgramName}, but got {len(params)}")

                for i in range(len(includedProgram.inputs)):
                    label = includedProgram.inputs[i]
                    param = params[i] if i < len(params) else None
                    providedInputs[label] = param
                inputData = {"startTimestamp": time.time(), "inputs": providedInputs}

                print("About to run program: ", includedProgramName)
                return ProgramExecutor(self.programDirectory).executeProgram(includedProgramName, inputData, preferredVisualType)
            else:
                # It's a value. Either a variable name or a literal value.
                if code_block in variables:
                    return variables[code_block]
                else:
                    # It's a literal value. Parse like a Python atomic literal
                    # First, remove the quotes
                    code_block = code_block.strip("\"'")
                    # Then, parse like a Python atomic literal
                    return eval(code_block)

        def convertToMarkdownStr(data: Any) -> str:
            if data is None:
                return ""
            elif isinstance(data, str):
                return data
            elif isinstance(data, int):
                return str(data)
            elif isinstance(data, float):
                return str(data)
            elif isinstance(data, dict):
                if data.visualReturnType == "html":
                    return data.visualOutput
                elif data.visualReturnType == "png":
                    # Be sure to base64 encode the png
                    return f"![{data.visualReturnType}](data:image/png;base64,{base64.b64encode(data.visualOutput).decode('utf-8')})"
                elif data.visualReturnType == None:
                    # Convert the dictionary to a markdown string
                    return "\n".join([f"{key}: {value}" for key, value in data.dataOutputs.items()])
                else:
                    raise ValueError(f"Invalid visual return type: {data.visualReturnType}")
            elif isinstance(data, list):
                return "\n".join([convertToMarkdownStr(item) for item in data])
            else:
                raise ValueError(f"Invalid data type during markdown preprocessing: {type(data)}")

        def preprocessBlock(code_block: str) -> str:
            # If the code block starts with "include", we need to preprocess the include and replace it with the included program's output
            # If the code block has an equals sign, we need to preprocess the variable assignment and replace it with nothing
            # If the code block is a standalone variable, we need to replace it with the variable's value
            return convertToMarkdownStr(processElement(code_block, variables))

        while "{{" in code:
            start = code.find("{{")
            end = code.find("}}")
            if start == -1 or end == -1:
                break
            # Get the code between the double-braces
            code_block = code[start+2:end]

            # Replace the double-brace block with the pre-processed version of the code
            code = code[:start] + preprocessBlock(code_block) + code[end+2:]

        return code

    def process(self, code: str, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

        # Preprocess the document
        finalizedMarkdown = self.__preprocess__(code, preferredVisualType=preferredVisualReturnType)
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






