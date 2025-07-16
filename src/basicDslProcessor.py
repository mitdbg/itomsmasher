from dslProcessor import DSLProcessor, EscapedSublanguageDSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import time
import base64
from markdown import markdown
from playwright.sync_api import sync_playwright

# BasicDSLProcessor is a DSL processor for the basic DSL
class BasicDSLProcessor(EscapedSublanguageDSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html"]
    
    def __convertToLocalDSL__(self, data: Any) -> str:
        "This converts a data item in the braced sublanguage to a representation that can be used in markdown."
        if data is None:
            return ""
        elif isinstance(data, str):
            return data
        elif isinstance(data, int):
            return str(data)
        elif isinstance(data, float):
            return str(data)
        elif isinstance(data, ProgramOutput):            
            # The returned item is an example of ProgramOutput
            if data.visualReturnType() == "html":
                return data.viz()
            elif data.visualReturnType() == "png":
                # Be sure to base64 encode the png
                return f"![{data.visualReturnType()}](data:image/png;base64,{base64.b64encode(data.viz()).decode('utf-8')})"
            else:
                # We can only convert these two visual return types to markdown
                raise ValueError(f"Invalid visual return type: {data.visualReturnType()}")
        elif isinstance(data, dict):
            #It's not a ProgramOutput. It's just a dictionary, so convert to a string representation
            return "\n".join([f"{key}: {value}" for key, value in data.items()])
        elif isinstance(data, list):
            return "[" + ",".join([self.__convertToLocalDSL__(item) for item in data]) + "]"
        else:
            # What else could it be?
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")

    def __postProcess__(self, postprocessedSourceCode: str, finalVariables: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        "This postprocesses the source code (after the braced sublanguage is processed). In this case, it's processed as markdown."
        html = markdown(postprocessedSourceCode)

        if preferredVisualReturnType == "html":
            outputData = {outputName: finalVariables[outputName] for outputName in outputNames}
            return ProgramOutput(time.time(), "html", html, outputData)
        
        elif preferredVisualReturnType == "png":
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html)
                png_bytes = page.screenshot(full_page=True, type="png")
                browser.close()
                outputData = {outputName: finalVariables[outputName] for outputName in outputNames}
                return ProgramOutput(time.time(), "png", png_bytes, outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")





