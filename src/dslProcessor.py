from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
import time, os, base64
import re
from typing import Optional, List, Tuple, Any

# DSLProcessor is a generic superclass for all DSL processors
class DSLProcessor:
    def __init__(self):
        pass

    def getVisualReturnTypes(self) -> List[str]:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def process(self, program: NamedProgram, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def runProgram(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = program.codeVersions[-1]
        latestExecutionHistory = program.executions[-1]
        programOutput = self.process(latestCode, input["inputs"], program.outputs, preferredVisualReturnType)
        latestExecutionHistory.append((input, programOutput))
        return programOutput

class EscapedSublanguageDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def __convertToLocalDSL__(self, data: Any) -> str:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def __preprocess__(self, code: str, input: dict, preferredVisualType: Optional[str] = None, startBlock: Optional[str] = "{{", endBlock: Optional[str] = "}}") -> Tuple[str, dict]:
        # Any part of the code in double-braces should be replaced with a pre-processed version of the code
        # Let's start by iterating through the code and finding all double-brace blocks
        # We'll replace each double-brace block with the pre-processed version of the code
        # We'll return the pre-processed code

        # initialize variables with contents of input (but make a copy)
        variables = input.copy()
        def processElement(code_block: str, variables: dict) -> Any:
            # Check if the code block is a variable assignment of the form varname = value. Use regex to match this.
            # It's OK if there is no whitespace before or after the equals sign
            if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*[ \t]*=[ \t]*.*$", code_block):
                # It's a variable assignment
                # Split the code block into lhs and rhs using the leftmost equals sign
                lhs, rhs = code_block.split("=", 1)
                lhs = lhs.strip()
                rhs = rhs.strip()

                rhsProcessed = processElement(rhs, variables)
                variables[lhs] = rhsProcessed
                return None
            
            # Check if the code block has a dotted field access. Must have at least one dot.
            elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$", code_block):
                # It's a variable access
                # Split the code block into varName and then remainder (of zero or more dotted names)
                lhs, rhs = code_block.split(".", 1)
                val = variables[lhs]
                parts = rhs.split(".")

                for part in parts:
                    if isinstance(val, ProgramOutput):
                        if part == "data":
                            val = val.data()
                        else:
                            raise ValueError(f"Invalid field: {part} for program output")
                    elif isinstance(val, dict):
                        val = val[part]
                    else:
                        raise ValueError(f"Invalid dotted field access: {code_block}")

                return val

            # Check if the code block is of the form {{include("programName", input0=value0, input1=value1, input2=value2)}}, where we might have zero or more 'input' parameters.
            # Use a regex to match this.
            elif re.match(r'include\(\s*"([^"]+)"\s*(?:,\s*([^)]+))?\)', code_block):
                # It's an include statement
                # Form of include is 'include("programName", input0=value0, input1=value1, input2=value2)'
                match = re.match(r'include\(\s*"([^"]+)"\s*(?:,\s*([^)]+))?\)', code_block)
                programName = match.group(1)
                paramList = match.group(2)
                if paramList is None:
                    paramList = []
                else:
                    paramList = paramList.split(",")
                # strip whitespace from all params
                paramList = [p.strip() for p in paramList]
                # parse the param list into a dictionary
                paramDict = {}
                for p in paramList:
                    key, value = p.split("=")
                    key = key.strip()
                    value = value.strip()
                    paramDict[key] = value
                includedProgramName = programName.strip("\"'")
                processedParamDict = {k: processElement(v, variables) for k, v in paramDict.items()}
                inputData = {"startTimestamp": time.time(), "inputs": processedParamDict}
                from programExecutor import ProgramExecutor
                return ProgramExecutor(self.programDirectory).executeProgram(includedProgramName, inputData, preferredVisualType)
            else:
                # It's a value. Either a variable name or a literal value.
                if code_block in variables:
                    return variables[code_block]
                else:
                    # It's a literal value. Parse like a Python atomic literal
                    if code_block == "":
                        return ""
                    else:
                        test = str(eval(code_block))
                        return test

        while startBlock in code:
            start = code.find(startBlock)
            end = code.find(endBlock)
            if start == -1 or end == -1:
                break
            # Get the code between the double-braces
            code_block = code[start+2:end]
            # Replace the double-brace block with the sublanguage-processed version of the code
            code = code[:start] + self.__convertToLocalDSL__(processElement(code_block, variables)) + code[end+2:]

        return code, variables

    def __postProcess__(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        raise NotImplementedError("EscapedSublanguageDSLProcessor is an abstract class and cannot be instantiated directly")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        # Preprocess the document
        preprocessedSourceCode, finalVariables = self.__preprocess__(code, input, preferredVisualReturnType)
        return self.__postProcess__(preprocessedSourceCode, finalVariables, outputNames, preferredVisualReturnType)

    
