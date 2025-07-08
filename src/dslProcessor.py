import time
from typing import List, Optional

from markdown import markdown
from playwright.sync_api import sync_playwright

from programs import ProgramInput, ProgramOutput


# DSLProcessor is a class that processes a DSL string and returns a string.
class DSLProcessor:
    def __init__(self):
        pass

    def getVisualReturnTypes(self) -> List[str]:
        pass

    def process(self, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        pass

class BasicDSLProcessor(DSLProcessor):
    def __init__(self):
        super().__init__()

    def getVisualReturnTypes(self) -> List[str]:
        return ["png", "html"]

    def __preprocess__(self, code: str) -> str:
        return code

    def process(self, code: str, input: ProgramInput, preferredVisualReturnType: Optional[str] = None) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

        # Preprocess the document
        finalizedMarkdown = self.__preprocess__(code)
        html = markdown(finalizedMarkdown)

        if preferredVisualReturnType == "html":
            return ProgramOutput(endTimestamp=time.time(),
                                 visualReturnType="html",
                                 visualOutput=html,
                                 dataOutputs={})
        
        elif preferredVisualReturnType == "png":
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html)
                png_bytes = page.screenshot(full_page=True, type="png")
                browser.close()
                return ProgramOutput(endTimestamp=time.time(),
                                     visualReturnType="png",
                                     visualOutput=png_bytes,
                                     dataOutputs={})
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")


