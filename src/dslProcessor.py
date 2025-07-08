#! /usr/bin/env python3


## DSLProcessor is a class that processes a DSL string and returns a string.
## NamedProgram is a class that represents a program with a name, description, DSL ID, code versions, inputs, and outputs.
import sys
import json
from typing import Optional, List, Tuple, TypedDict

class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

class ProgramOutput(TypedDict):
    endTimestamp: int
    outputs: TypedDict

# DSLProcessor is a class that processes a DSL string and returns a string.
class DSLProcessor:
    def __init__(self):
        pass

    def process(self, input: ProgramInput) -> ProgramOutput:
        pass

class BasicDSLProcessor(DSLProcessor):
    def __init__(self):
        super().__init__()

    def process(self, code: str, input: ProgramInput) -> ProgramOutput:
        raise NotImplementedError("BasicDSLProcessor is not implemented")

# global instance of DSLProcessor
basicDSLProcessor = BasicDSLProcessor()
availableDSLProcessors = {
    "basic": basicDSLProcessor
}

# NamedProgram is a class that represents a program with a name, description, DSL ID, code versions, inputs, and outputs.
class NamedProgram:
    def __init__(self, name: str, 
                 description: str, 
                 dslId: str, 
                 codeVersions: Optional[List[str]] = None,
                 executions: Optional[List[List[Tuple[ProgramInput, ProgramOutput]]]] = None):
        self.name = name
        self.description = description
        self.dslId = dslId
        self.codeVersions = codeVersions or []
        self.executions = executions or []

        if self.dslId not in availableDSLProcessors:
            raise ValueError(f"DSL processor {self.dslId} not found")
        self.dslProcessor = availableDSLProcessors[self.dslId]

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

    def addCodeVersion(self, newCode: str) -> None:
        self.codeVersions.append(newCode)
        self.executions.append([])

    def runProgram(self, input: ProgramInput) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = self.codeVersions[-1]
        latestExecutionHistory = self.executions[-1]

        execution = (input, ProgramOutput(endTimestamp=0, outputs={}))
        latestExecutionHistory.append(execution)
        output = self.dslProcessor.process(latestCode, input)
        execution.output = output
        return output
    
# main
def main():
    pass

if __name__ == "__main__":
    # Pass in the name of a program text file

    # Grab the first argument as the program name
    programFile = sys.argv[1]
    programName = programFile.split("/")[-1].split(".")[0]

    # Load the program from the file
    namedProgram = NamedProgram(programName, "Loaded from file {programFile}", "basic")
    namedProgram.addCodeVersion(open(programFile).read())

    namedProgram.runProgram(ProgramInput(startTimestamp=0, inputs={}))

# DSL #1: Markdown plus variables, and object inclusions
# # Welcome to the world of Bubble Sort
# ## The theory
# We want to take a list of numbers and sort them in ascending order.
# The core idea of bubble sort is to iterate through the list and swap adjacent elements if they are in the wrong order.
#
# Imagine we have a list of numbers:
# {{numbers = [5, 3, 8, 4, 2]}}
# {{numbers}}
#
# Too bad they're out of order! What does bubble sort do?
# Imagine we start at positions 0 and 1.
# The first two numbers are numbers[0] and numbers[1]. Let's see what happens after one iteration of bubble sort.
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=1)}}
#
# {{newNumbers}}
#
# We can see that the first two numbers are swapped.
# 
# Now let's try the second step.
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=2)}}
#
# {{newNumbers}}
#
# We are now comparing 5 and 8. These are in the correct order, so we move on to the next pair.
#
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=3)}}
#
# {{include("/itomsmasher/arrayRender", newNumbers)}}
#
# We are now comparing 8 and 4. These are in the wrong order, so we swap them.
#
# We can render the full bubble sort process by setting steps to the length of the list.
# {{include("/itomsmasher/bubbleSortAnimate", numbers)}}
#
# {{return None}}



# DSL #2: VegaLite plus variables, and object inclusions

