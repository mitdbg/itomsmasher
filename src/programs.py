import sys
import json
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
    def __init__(self):
        self.programs = {}

    def addProgram(self, program: NamedProgram) -> None:
        if program.name in self.programs:
            raise ValueError(f"Program {program.name} already exists")
        self.programs[program.name] = program

    def getProgram(self, programName: str) -> NamedProgram:
        if programName not in self.programs:
            raise ValueError(f"Program {programName} not found")
        return self.programs[programName]


