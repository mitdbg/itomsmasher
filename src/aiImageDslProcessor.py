<<<<<<< HEAD
from dslProcessor import PreprocessedDSL
=======
from dslProcessor import BasicDSLProcessor
>>>>>>> ddb2032fcf482ac0b59c20ab67ecf72ac591e864
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import os
import time
import base64
import requests
from dotenv import dotenv_values

class AIImageProcessor(PreprocessedDSL):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html", "md"]


    def postprocess(self, processedCode: str, processedOutputState: dict, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> ProgramOutput:
        size = input["size"] if "size" in input else "large"
        if size == "small":
            horizontalSize = 256
            verticalSize = 256
        elif size == "medium":
            horizontalSize = 512
            verticalSize = 512
        elif size == "large":
            horizontalSize = 1024
            verticalSize = 1024
        else:
            raise ValueError(f"Invalid size: {size}. Must be one of 'small', 'medium', or 'large'.")

        import requests

        api_key = None
        if os.path.exists(".env"):
            env = dotenv_values(".env")
            api_key = env["OPENAI_API_KEY"]
        else:
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Call OpenAI API to generate image
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "prompt": processedCode,
            "n": 1,
            "size": f"{horizontalSize}x{verticalSize}",
            "response_format": "b64_json"
        }

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")

        # Get base64 encoded image and convert to bytes
        image_data = response.json()["data"][0]["b64_json"]
        png_bytes = base64.b64decode(image_data)
        outputData = {}

        if ("_forceformat" in input):
            preferredVisualReturnType = input["_forceformat"]

        if preferredVisualReturnType == "png":
            return ProgramOutput(time.time(), "png", png_bytes, outputData)
        elif preferredVisualReturnType == "html":               # Return an HTML image tag that b64 encodes the image directly
            return ProgramOutput(time.time(), "html", f"<img src='data:image/png;base64,{image_data}' />", outputData)
        elif preferredVisualReturnType == "md":
            return ProgramOutput(time.time(), "md", f"![Image](data:image/png;base64,{image_data})", outputData)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
