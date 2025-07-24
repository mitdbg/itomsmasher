from dslProcessor import BasicDSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import time
import base64
import altair as alt
import json
import uuid
import os

# VegaDSLProcessor is a DSL processor for the Vega DSL
class VegaDSLProcessor(BasicDSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html","svg","pdf","json","md"]
    
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str,config:dict) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        
        # do the templating stuff
        result = super().process(code, input, outputNames, "md",config)
        if not result.succeeded():
            return dict(error="ERROR: program failed with message: " + result.errorMessage(),
                        succeeded=False)
        else:
            code = str(result.viz())

        if "_forceformat" in input:
            preferredVisualReturnType = input["_forceformat"]

        #print(f"code: {code}")
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
            os.remove(f"{guid}.out")

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
        




        





