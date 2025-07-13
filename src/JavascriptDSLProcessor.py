from dslProcessor import EscapedSublanguageDSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Dict
import time
import re
from playwright.sync_api import sync_playwright
import pythonmonkey as pm
from typing import List, Any
import base64
#need to fix this for return types/rendering

class JavascriptDSLProcessor(EscapedSublanguageDSLProcessor):

    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)
    
    def getVisualReturnTypes(self) -> List[str]:
        return ["html", "png"]

    def __convertToLocalDSL__(self, data: Any) -> str:
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
            return "\n".join([self.__convertToLocalDSL__(item) for item in data])
        else:
            # What else could it be?
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")
        
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        
        javascriptcode, finalVariables = self.__preprocess__(code, input, preferredVisualReturnType, startBlock="-#", endBlock="#-")

        #print(javascriptcode);

        retcode = pm.eval(javascriptcode);
        val = retcode();
        #print(val);

        # Extract output data
        outputData = {}
        for outputName in outputNames:
            outputData[outputName] = val
        
        if preferredVisualReturnType == "html":
            return ProgramOutput(time.time(), preferredVisualReturnType, javascriptcode, outputData)
        elif preferredVisualReturnType == "png":
            return ProgramOutput(time.time(), preferredVisualReturnType, self._generatePng(val), outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
    

    def _generatePng(self, outputval: Any) -> bytes:
        """Generate PNG image from grid (simple text-based)"""
        # For now, return HTML as PNG would require additional dependencies
        html = "<body>" + str(outputval) + "</body>"

        # Convert HTML to PNG
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            png_bytes = page.screenshot(full_page=True, type="png")
            browser.close()
            return png_bytes














