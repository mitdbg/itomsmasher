from openai import OpenAI
import hashlib
import os
from dslProcessor import BasicDSLProcessor
from programs import ProgramOutput, ProgramDirectory, TracerNode
from typing import List, Any, Optional
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright
import json
import time

class LLMDSLProcessor(BasicDSLProcessor):
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
        
        model = "gpt-4o-mini"
        if "model" in config:
            model = config["model"]

        prompt = result.viz()

        client = None
        # if .env exists, load it
        if os.path.exists(".env"):
            env = dotenv_values(".env")
            client = OpenAI(api_key=env["OPENAI_API_KEY"])
        else:
            client = OpenAI()

        llm_cache = ".llm_cache"
        # create a speech_cache folder if it doesn't exist
        if not os.path.exists(llm_cache):
            os.makedirs(llm_cache)
        
        # create a hash of the prompt
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        # create a file name for the prompt
        prompt_file = os.path.join(llm_cache, f"{prompt_hash}.txt")
        
        # if the prompt file exists, read it
        response = None
        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as file:
                response = file.read()
        else:
            # generate the prompt

            serv_resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            response = serv_resp.choices[0].message.content
            # save the prompt to the file
            with open(prompt_file, "w") as file:
                file.write(response)

        # split at ```json
        result = json.loads(response.split("```json")[1].split("```")[0])

        outputData = {}
        table = "<TABLE><TR><TH>Key</TH><TH>Value</TH></TR>\n"
        markdown_table = "| Key | Value |\n| --- | --- |\n"
        #print(outputNames)
        for key, value in result.items():
            # if the key is in outputNames, add it to the outputData
            if key in outputNames:
                outputData[key] = value
                table += f"<TR><TD>{key}</TD><TD>{value}</TD></TR>\n"
                markdown_table += f"| {key} | {value} |\n"
        table += "</TABLE>"

        if preferredVisualReturnType == "html":
            # Return an HTML image tag that b64 encodes the image directly
            return ProgramOutput(time.time(), "html", f"{table}", outputData)
        elif preferredVisualReturnType == "md":
            return ProgramOutput(time.time(), "md", f"{markdown_table}", outputData)
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
