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
    def __init__(self, name: str, 
                 description: str, 
                 dslId: str, 
                 inputs: List[str],
                 codeVersions: Optional[List[str]] = None,
                 executions: Optional[List[List[Tuple[ProgramInput, ProgramOutput]]]] = None):
        self.name = name
        self.description = description
        self.dslId = dslId
        self.inputs = inputs
        self.codeVersions = codeVersions or [""]
        self.executions = executions or [[]]

    # init from dict
    @classmethod
    def from_dict(cls, dict: dict) -> "NamedProgram":
        return cls(dict["name"], 
                   dict["description"], 
                   dict["dslId"], 
                   dict["inputs"],
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
            "codeVersions": self.codeVersions,
            "executions": self.executions
        })

    def getLatestCode(self) -> str:
        return self.codeVersions[-1]

    def getExecutionHistory(self) -> List[Tuple[ProgramInput, ProgramOutput]]:
        return self.executions[-1]

    def getLatestExecution(self) -> Tuple[ProgramInput, ProgramOutput]:
        return self.executions[-1][-1]

    def addCodeVersion(self, newCode: str) -> None:
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
                        self.__addProgram__(program)

        self.saveAndRefresh()

    def saveAndRefresh(self) -> None:
        for programName, program in self.programs.items():
            programDir = os.path.join(self.localProgramDir, programName)
            if not os.path.exists(programDir):
                os.makedirs(programDir)

            # Create the code file if it doesn't exist
            codeFile = os.path.join(programDir, "code.itom")
            if not os.path.exists(codeFile):
                with open(codeFile, "w") as f:
                    f.write(program.getLatestCode())
            else:
                # Load the code file and update the program if it has changed
                with open(codeFile, "r") as f:
                    codeText = f.read()
                    if codeText != program.getLatestCode():
                        program.addCodeVersion(codeText)

            # Write out the program JSON file
            with open(os.path.join(self.localProgramDir, programName, "program.json"), "w") as f:
                f.write(program.toJson())

    def __addProgram__(self, program: NamedProgram) -> None:
        if program.name in self.programs:
            raise ValueError(f"Program {program.name} already exists")
        self.programs[program.name] = program

    def addNewProgram(self, programName: str, metadataComment: str, code: str) -> None:
        # REMIND: We need to modify this so it does not rely on metadata from the invoker. Instead, things
        # like dslId description, and inputs should be read from the code header.

        # Read the code header to get the description, dslId, inputs, and outputs.
        # The header is a list of #@-prefixed lines. Each line is a key-value pair of the form "key: value".
        # The header should be removed from the code text.
        # Once we hit a line that is not prefixed with #@, we stop parsing the header.

        header = []
        inHeader = True
        remainingCode = []
        for line in code.split("\n"):
            if inHeader and line.startswith("#@"):
                # Remove the #@ prefix
                line = line[2:]
                header.append(line)
            else:
                inHeader = False
                remainingCode.append(line)

        # Parse the header
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

        program = NamedProgram(programName, description, dslId, inputs, outputs)
        program.addCodeVersion("\n".join(remainingCode))
        self.__addProgram__(program)
        self.saveAndRefresh()

    def getPrograms(self) -> List[NamedProgram]:
        return list(self.programs.values())

    def getProgram(self, programName: str) -> NamedProgram:
        if programName not in self.programs:
            raise ValueError(f"Program {programName} not found")
        return self.programs[programName]


