from typing import Optional, List, Tuple, TypedDict, Any

class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

class ProgramOutput(TypedDict):
    endTimestamp: int
    visualReturnType: str
    visualOutput: Any
    dataOutputs: TypedDict

