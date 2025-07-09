import sys
import json
import os
from typing import Optional, List, Tuple, TypedDict, Any

# ProgramInput is a class that represents the input of a program
class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

# ProgramOutput is a class that represents the output of a program
class ProgramOutput(TypedDict):
    endTimestamp: int
    visualReturnType: str
    visualOutput: Any
    dataOutputs: TypedDict

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

    def addNewProgram(self, programName: str, description: str, dslId: str, inputs: List[str], code: str) -> None:
        program = NamedProgram(programName, description, dslId, inputs)
        program.addCodeVersion(code)
        self.__addProgram__(program)
        self.saveAndRefresh()

    def getProgram(self, programName: str) -> NamedProgram:
        if programName not in self.programs:
            raise ValueError(f"Program {programName} not found")
        return self.programs[programName]


