from openai import OpenAI
import cv2
import hashlib
import os
from pydub import AudioSegment
import uuid
from dslProcessor import DSLProcessor, BasicDSLProcessor
from programs import ProgramOutput, ProgramDirectory, TracerNode
from typing import List, Any, Optional
import os
import time
import shutil

class SlideDSLProcessor(BasicDSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)
        self.programDirectory = programDirectory
    
    def getVisualReturnTypes(self) -> List[str]:
        return ["html","md"]
    
    def getIncludableTypes(self) -> List[str]:
        return ["html", "png", "md"]
    
    def postprocess(self, processedCode: str, processedOutputState: dict, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict,tracer: Optional[TracerNode] = None) -> ProgramOutput:
        result = super().postprocess(processedCode, processedOutputState, input, outputNames, "md",config,tracer)
        if not result.succeeded():
            return dict(error="ERROR: program failed with message: " + result.errorMessage(),
                        succeeded=False)
        else:
            code =str(result.viz())
            

        # create a random id for the temp directory
        guid = str(uuid.uuid4())
        infile = f"{guid}.md"
        outfile = f"{guid}.html"
        prepend = "---\nmarp: true\ntheme: custom-default\n---\n"

        # save the code to a temporary file
        with open(infile, "w") as file:
            file.write(prepend + code)

        # if the the preferred visual return type is html, run the marp command to crate the html
        if preferredVisualReturnType == "html":
            result = os.system(f"marp {infile} -o {outfile} --html --allow-local-files")
            
            # Check if marp command succeeded and html file was created
            if result == 0 and os.path.exists(outfile):
                # read the html file into a string
                with open(outfile, "r") as file:
                    html_string = file.read()
            else:
                # Fallback: marp failed, return error or use markdown
                return ProgramOutput(time.time(), "error", f"Marp command failed. HTML file not generated. Exit code: {result}", {})

        with open(infile, "r") as file:
            md_string = file.read()

        # delete the temp files
        # if infile exists, delete it
        if os.path.exists(infile):
            os.remove(infile)
        # if outfile exists, delete it
        if os.path.exists(outfile):
            os.remove(outfile)

        # return the html string
        if preferredVisualReturnType == "html":
            return ProgramOutput(time.time(), "html", html_string, {})
        elif preferredVisualReturnType == "md":
            return ProgramOutput(time.time(), "md", md_string, {})
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        




