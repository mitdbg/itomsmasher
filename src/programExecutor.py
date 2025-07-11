from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
from dslProcessor import DSLProcessor
from basicDslProcessor import BasicDSLProcessor
from aiImageDslProcessor import AIImageProcessor
from spreadsheetDslProcessor import SpreadsheetDSLProcessor
from VegaDSLProcessor import VegaDSLProcessor
from JavascriptDSLProcessor import JavascriptDSLProcessor
from typing import Optional

# ProgramExecutor is a class that executes a program of any kind
class ProgramExecutor:
    def __init__(self, programDirectory: ProgramDirectory):
        self.programDirectory = programDirectory
        self.availableDSLProcessors = {
            "basic": BasicDSLProcessor(programDirectory),
            "aiimage": AIImageProcessor(programDirectory),
            "spreadsheet": SpreadsheetDSLProcessor(programDirectory),
            "vega-lite": VegaDSLProcessor(programDirectory),
            "javascript": JavascriptDSLProcessor(programDirectory)
        }

    def executeProgram(self, programName: str, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        program = self.programDirectory.getProgram(programName)
        if program.dslId not in self.availableDSLProcessors:
            raise ValueError(f"DSL processor {program.dslId} not found")

        dslProcessor = self.availableDSLProcessors[program.dslId]
        return dslProcessor.runProgram(program, input, preferredVisualReturnType)

