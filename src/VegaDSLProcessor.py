from dslProcessor import DSLProcessor,EscapedSublanguageDSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import time
import base64
import vl_convert as vlc

# VegaDSLProcessor is a DSL processor for the Vega DSL
class VegaDSLProcessor(EscapedSublanguageDSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html"]
    
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
            return "[" + ",".join([self.__convertToLocalDSL__(item) for item in data]) + "]"
        else:
            # What else could it be?
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

        # Preprocess the document
        vl_spec, finalVariables = self.__preprocess__(code, input, preferredVisualReturnType, startBlock="-#", endBlock="#-")
        
        # convert the vl_spec to a raw python string
        vl_spec = r"{}".format(vl_spec)
        #print("--",vl_spec,"--")

        if preferredVisualReturnType == "html":
            png_data = vlc.vegalite_to_png(vl_spec=vl_spec, scale=2)
            outputData = {outputName: finalVariables[outputName] for outputName in outputNames}
            return ProgramOutput(time.time(), 
                                 "html", 
                                 # Fix up the png data to be a base64 encoded string
                                 f"<img src='data:image/png;base64,{base64.b64encode(png_data).decode('utf-8')}' />",
                                 outputData)
        elif preferredVisualReturnType == "png":
            png_data = vlc.vegalite_to_png(vl_spec=vl_spec, scale=2)
            outputData = {outputName: finalVariables[outputName] for outputName in outputNames}
            return ProgramOutput(time.time(), "png", png_data, outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")





