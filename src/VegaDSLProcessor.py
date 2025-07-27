from dslProcessor import BasicDSLProcessor, PreprocessedDSL
from programs import ProgramOutput, ProgramDirectory, TracerNode
from typing import List, Any, Optional
import time
import base64
import altair as alt
import json
import uuid
import os

# VegaDSLProcessor is a DSL processor for the Vega DSL
class VegaDSLProcessor(PreprocessedDSL):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html","svg","pdf","json","md"]
    
    def getIncludableTypes(self) -> List[str]:
        return ["html", "png"]
    
    def postprocess(self, processedCode: str, processedOutputState: dict, input: dict, outputNames: List[str], preferredVisualReturnType: str, config: dict,tracer: Optional[TracerNode] = None) -> ProgramOutput:
        code = processedCode
        chart_json = json.loads(str(code))
        
        # just want json, so we can be done
        if preferredVisualReturnType == "json":
            return ProgramOutput(time.time(), "json", chart_json, {})
        
        # make the chart
        chart = alt.Chart.from_json(json.dumps(chart_json))

        # create a guid 
        guid = str(uuid.uuid4())
        binary_data = None

        if preferredVisualReturnType == "html":
            chart.save(f"{guid}.out",format="html")
        elif preferredVisualReturnType == "png":
            chart.save(f"{guid}.out",format="png")
        elif preferredVisualReturnType == "svg":
            chart.save(f"{guid}.out",format="svg")
        elif preferredVisualReturnType == "pdf":
            chart.save(f"{guid}.out",format="pdf")
        elif preferredVisualReturnType == "md":
            chart.save(f"{guid}.out",format="png")
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

        # load the binary data from the file {guid}.out
        with open(f"{guid}.out", "rb") as file:
            binary_data = file.read()

        

        # remove the guid file {guid}.out if it exists
        if os.path.exists(f"{guid}.out"):
            #os.remove(f"{guid}.out")
            pass

        outputData = {}

        if preferredVisualReturnType == "html":
            # create a text_data version
            text_data = binary_data.decode('utf-8')
            return ProgramOutput(time.time(), "html", text_data, {})
        elif preferredVisualReturnType == "png":
            return ProgramOutput(time.time(), "png", binary_data, {})
        elif preferredVisualReturnType == "svg":
            text_data = binary_data.decode('utf-8')
            return ProgramOutput(time.time(), "svg", text_data, {})
        elif preferredVisualReturnType == "pdf":
            return ProgramOutput(time.time(), "pdf", binary_data, {})
        elif preferredVisualReturnType == "md":
            image_data = base64.b64encode(binary_data).decode('utf-8')
            return ProgramOutput(time.time(), "md", f"![Image](data:image/png;base64,{image_data})", outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        




        





