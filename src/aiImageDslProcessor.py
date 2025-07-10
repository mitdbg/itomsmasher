from dslProcessor import DSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Any
import os
import time
import base64
import requests

class AIImageProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["png"]

    def __convertToLocalDSL__(self, data: Any) -> str:
        if data is None:
            return ""
        elif isinstance(data, str):
            return data
        else:
            raise ValueError(f"Invalid return type during markdown preprocessing: {data}")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        # Contact ChatGPT to generate an image based on the text in the code
        # Return the image as a ProgramOutput

        # Preprocess the code so that all variables are replaced with their values
        code, finalVariables = self.__preprocess__(code, input, preferredVisualReturnType)

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

        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Call OpenAI API to generate image
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "prompt": code,
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
        outputData = {outputName: finalVariables[outputName] for outputName in outputNames}
        return ProgramOutput(time.time(), "png", png_bytes, outputData)