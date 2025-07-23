from dslProcessor import DSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import os
import time
from playwright.sync_api import sync_playwright
import base64
import requests

class PythonDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["html","png"]

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str,config:dict) -> ProgramOutput:
        main_function_name = config['mainfunc']
        scope = {}
        exec(code)

        # create a function call string
        args = []
        for key, value in input.items():
            val = str(value)
            args.append(f"{key}={val}")
        args_string = ", ".join(args)

        # create a function call string
        function_call = f"{main_function_name}({args_string})"

        #print("function_call", function_call)
        result = eval(function_call)
        #print("result", result)
        outputData = {}
        table = "<TABLE><TR><TH>Key</TH><TH>Value</TH></TR>\n"
        for key, value in result.items():
            # if the key is in outputNames, add it to the outputData
            if key in outputNames:
                outputData[key] = value
                table += f"<TR><TD>{key}</TD><TD>{value}</TD></TR>\n"
        table += "</TABLE>"

        if preferredVisualReturnType == "html":
            # Return an HTML image tag that b64 encodes the image directly
            return ProgramOutput(time.time(), "html", f"{table}", outputData)
        elif preferredVisualReturnType == "png":
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(table)
                png_bytes = page.screenshot(full_page=True, type="png")
                browser.close()
                return ProgramOutput(time.time(), "png", png_bytes, outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
