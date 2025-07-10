import sys
import json
import os
from typing import Optional, List, Tuple, TypedDict, Any

# ProgramInput is a class that represents the input of a program
class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

# ProgramOutput is a class that represents the output of a program
class ProgramOutput:
    def __init__(self, endTimestamp: int, visualReturnType: str, visualOutput: Any, dataOutputs: TypedDict):
        self.__endTimestamp = endTimestamp
        self.__visualReturnType = visualReturnType
        self.__visualOutput = visualOutput
        self.__dataOutputs = dataOutputs

    def endTimestamp(self) -> int:
        return self.__endTimestamp
    
    def viz(self) -> Any:
        return self.__visualOutput
    
    def visualReturnType(self) -> str:
        return self.__visualReturnType
    
    def data(self) -> TypedDict:
        return self.__dataOutputs

# NamedProgram is a class that represents a program with a 
# name, description, DSL ID, code versions, inputs, and outputs.
class NamedProgram:
    def __init__(self, 
                 name: str, 
                 description: str,
                 dslId: str,
                 inputs: List[str],
                 outputs: List[str],
                 rawCodeVersions: List[str],
                 codeVersions: List[str],
                 executions: List[List[Tuple[ProgramInput, ProgramOutput]]]):
        self.name = name
        self.description = description
        self.dslId = dslId
        self.inputs = inputs
        self.outputs = outputs
        self.rawCodeVersions = rawCodeVersions
        self.codeVersions = codeVersions
        self.executions = executions

    @classmethod
    def __processCodeHeader__(cls, code: str) -> Tuple[str, str, str, List[str], List[str]]:
        # Read the code header to get the description, dslId, inputs, and outputs.
        # The header is a list of #@-prefixed lines. Each line is a key-value pair of the form "key: value".
        # The header should be removed from the code text.
        # Once we hit a line that is not prefixed with #@, we stop parsing the header.
        header = []
        inHeader = True
        remainingCodeLines = []
        for line in code.split("\n"):
            if inHeader and line.startswith("#@"):
                # Remove the #@ prefix
                line = line[2:]
                header.append(line)
            else:
                inHeader = False
                remainingCodeLines.append(line)

        # Parse the header
        remainingCode = "\n".join(remainingCodeLines)
        description = ""
        dslId = None
        inputs = []
        outputs = []
        for line in header:
            key, value = line.split(":")
            key = key.strip()
            value = value.strip()
            if key == "description":
                description += value + "\n"
            elif key == "dsl":
                if dslId is not None:
                    raise ValueError(f"Multiple dslId values in header: {dslId} and {value}")
                dslId = value
            elif key == "input":
                inputs.append(value)
            elif key == "output":
                outputs.append(value)
            else:
                raise ValueError(f"Unknown header key: {key}")

        if dslId is None:
            raise ValueError("No dslId found in header")

        return remainingCode, description, dslId, inputs, outputs


    @classmethod
    def from_code(cls, name: str, rawCode: str) -> "NamedProgram":
        remainingCode, description, dslId, inputs, outputs = cls.__processCodeHeader__(rawCode)
        return cls(name, description, dslId, inputs, outputs, [rawCode], [remainingCode], [[]])

    # init from dict
    @classmethod
    def from_dict(cls, dict: dict) -> "NamedProgram":
        return cls(dict["name"], 
                   dict["description"], 
                   dict["dslId"], 
                   dict["inputs"],
                   dict["outputs"],
                   dict["rawCodeVersions"],
                   dict["codeVersions"],
                   dict["executions"])

    # init from json
    @classmethod
    def from_json(cls, json_str: str) -> "NamedProgram":
        return cls.from_dict(json.loads(json_str))

    # save to json
    def toJson(self) -> str:
        return json.dumps({
            "name": self.name,
            "description": self.description,
            "dslId": self.dslId,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "rawCodeVersions": self.rawCodeVersions,
            "codeVersions": self.codeVersions,
            "executions": self.executions
        })

    def getLatestCode(self) -> str:
        return self.codeVersions[-1]
    
    def getLatestRawCode(self) -> str:
        return self.rawCodeVersions[-1]

    def getExecutionHistory(self) -> List[Tuple[ProgramInput, ProgramOutput]]:
        return self.executions[-1]

    def getLatestExecution(self) -> Tuple[ProgramInput, ProgramOutput]:
        return self.executions[-1][-1]

    def addCodeVersion(self, newRawCode: str, newCode: str) -> None:
        self.rawCodeVersions.append(newRawCode)
        self.codeVersions.append(newCode)
        self.executions.append([])

# ProgramDirectory is a class that stores all the programs in the system
class ProgramDirectory:
    def __init__(self, localProgramDir: str):
        self.programs = {}
        self.localProgramDir = localProgramDir

        # Each program has its own directory, so we need to list all the directories in the program directory
        for file in os.listdir(localProgramDir):
            if os.path.isdir(os.path.join(localProgramDir, file)):
                # Find json file in the directory
                jsonFile = os.path.join(localProgramDir, file, "program.json")
                if os.path.exists(jsonFile):
                    # Load the json file
                    with open(jsonFile, "r") as f:
                        program = NamedProgram.from_dict(json.load(f))
                        if program.name in self.programs:
                            raise ValueError(f"Program {program.name} already exists")
                        self.programs[program.name] = program

        self.__refresh__()

    def save(self) -> None:
        for programName, program in self.programs.items():
            programDir = os.path.join(self.localProgramDir, programName)
            if not os.path.exists(programDir):
                os.makedirs(programDir)

            # Create the code file if it doesn't exist
            codeFile = os.path.join(programDir, "code.itom")
            if not os.path.exists(codeFile):
                with open(codeFile, "w") as f:
                    f.write(program.getLatestRawCode())

            # Write out the program JSON file
            with open(os.path.join(self.localProgramDir, programName, "program.json"), "w") as f:
                f.write(program.toJson())

    def __refresh__(self) -> None:
        changed = False
        for programName, program in self.programs.items():
            # Load the code file and update the program if it has changed
            programDir = os.path.join(self.localProgramDir, programName)
            with open(os.path.join(programDir, "code.itom"), "r") as f:
                rawCodeText = f.read()
                if rawCodeText != program.getLatestRawCode():
                    remainingCode, description, dslId, inputs, outputs = NamedProgram.__processCodeHeader__(rawCodeText)
                    program.addCodeVersion(rawCodeText, remainingCode)
                    program.description = description
                    program.dslId = dslId
                    program.inputs = inputs
                    program.outputs = outputs
                    changed = True
        if changed:
            self.save()

    def addNewProgram(self, programName: str, metadataComment: str, rawCode: str, refresh: bool = False) -> None:
        if programName not in self.programs:
            program = NamedProgram.from_code(programName, rawCode)
            self.programs[program.name] = program
            self.save()
        else:
            if not refresh:
                raise ValueError(f"Program {programName} already exists")
            else:
                # Copy the new program source file (code.itom)to the program directory and refresh
                program = self.programs[programName]
                if program.getLatestRawCode() != rawCode:
                    programDir = os.path.join(self.localProgramDir, programName)
                    if os.path.exists(programDir):
                        # Copy the new program source file (code.itom) to the program directory
                        with open(os.path.join(programDir, "code.itom"), "w") as f:
                            f.write(rawCode)

                    print(f"Updating program {programName}")
                    self.__refresh__()



    def getPrograms(self) -> List[NamedProgram]:
        return list(self.programs.values())

    def getProgram(self, programName: str) -> NamedProgram:
        if programName not in self.programs:
            raise ValueError(f"Program {programName} not found")
        return self.programs[programName]


