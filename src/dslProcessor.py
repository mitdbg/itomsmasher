# 

from typing import TypedDict

class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

class ProgramOutput(TypedDict):
    endTimestamp: int
    outputs: TypedDict

# DSLProcessor is a class that processes a DSL string and returns a string.
class DSLProcessor:
    def __init__(self, program: str):
        self.program = program

    def process(self, input: ProgramInput) -> ProgramOutput:
        pass

# global instance of DSLProcessor
dslProcessor = DSLProcessor()


# NamedProgram is a class that represents a program with a name, description, DSL ID, code versions, inputs, and outputs.
class NamedProgram:
    def __init__(self, name: str, 
                 description: str, 
                 dslId: str, 
                 codeVersions: Optional[List[str]] = None,
                 executions = Optional[List[List[Tuple[ProgramInput, ProgramOutput]]]] = None):
        self.name = name
        self.description = description
        self.dslId = dslId
        self.codeVersions = codeVersions or []
        self.executions = executions or []

    # init from dict
    @classmethod
    def from_dict(cls, dict: dict) -> "NamedProgram":
        return cls(dict["name"], 
                   dict["description"], 
                   dict["dslId"], 
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
            "codeVersions": self.codeVersions,
            "executions": self.executions
        })

    def getLatestCode(self) -> str:
        return self.codeVersions[-1]

    def getExecutionHistory(self) -> List[Tuple[ProgramInput, ProgramOutput]]:
        return self.executions[-1]

    def getLatestExecution(self) -> Tuple[ProgramInput, ProgramOutput]:
        return self.executions[-1][-1]

    def applyEdits(self, newCode: str) -> None:
        self.codeVersions.append(newCode)
        self.executions.append([])

    def runProgram(self, input: ProgramInput) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = self.codeVersions[-1]
        latestExecutionHistory = self.executions[-1]

        execution = (input, ProgramOutput(endTimestamp=0, outputs={}))
        latestExecutionHistory.append(execution)
        output = dslProcessor.process(latestCode, input)
        execution.output = output
        return output

