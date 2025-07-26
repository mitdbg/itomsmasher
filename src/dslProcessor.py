from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
import time, os, base64
import re
from typing import Optional, List, Tuple, Any
import markdown as mdlib
import copy
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# DSLProcessor is a generic superclass for all DSL processors
class DSLProcessor:
    def __init__(self):
        pass

    def getVisualReturnTypes(self) -> List[str]:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")
    
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> ProgramOutput:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def runProgram(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType, config:dict) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = program.codeVersions[-1]
        latestExecutionHistory = program.executions[-1]
        programOutput = self.process(latestCode, input["inputs"], program.outputs, preferredVisualReturnType, config)
        latestExecutionHistory.append((input, programOutput))
        return programOutput

class PreprocessedDSL(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getIncludableTypes(self) -> List[str]:
        raise NotImplementedError("PreprocessedDSL is an abstract class and cannot be instantiated directly")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> ProgramOutput:
        processedCode, processedOutput = self.preprocess(code, input, outputNames, preferredVisualReturnType, config)
        return self.postprocess(processedCode, processedOutput, input, outputNames, preferredVisualReturnType, config)

    def postprocess(self, processedCode: str, processedOutputState: dict, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> ProgramOutput:
        raise NotImplementedError("PreprocessedDSL is an abstract class and cannot be instantiated directly")

    def preprocess(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> Tuple[str, dict]:
        # Use Jinja to process the document
        from jinja2 import Environment, BaseLoader, pass_context

        outputState = {}
        inputState = copy.deepcopy(input)
        env = Environment(loader=BaseLoader)

        macroText = """
        {% macro render_grid(spans) %}
        {% set columnCount = spans | sum %}
        {% set cell_list = caller().split('::cell') %}
        <div class="grid" style="display: grid; grid-template-columns: repeat({{columnCount}}, 1fr); gap: 0.25em;">    
            {% for cell in cell_list %}
        <div class="cell" style="grid-column: span {{spans[loop.index0 % spans|length]}}; display: flex; align-items: center; justify-content: center; text-align: center">
        {{ cell | trim }}
        </div>
            {% endfor %}
        </div>
        {% endmacro %}

        {% macro panel() %}
        <div class="panel">    
        {{ caller() }}
        </div>
        {% endmacro %}
        """

        # The return_variable function is used to return results from a module invocation
        @pass_context
        def return_variable(ctx, name, value):
            outputState[name] = value
            return ""

        # The include function is used to execute a module and obtain its returned results
        @pass_context
        def includeFn(ctx, *args, **kwargs) -> dict:
            if len(args) < 1:
                return dict(error="ERROR: includeFn must indicate programName",
                            succeeded=False)

            programName = args[0]
            try:
                program = self.programDirectory.getProgram(programName)
            except ValueError as e:
                return dict(error="ERROR: includeFn could not find program: " + programName,
                            succeeded=False)

            moduleInputs = {}
            providedInputs = dict(kwargs)
            for inputName in program.inputs.keys():
                if inputName not in providedInputs:
                    return dict(error="ERROR: includeFn could not find input: " + inputName,
                                succeeded=False)
                moduleInputs[inputName] = providedInputs[inputName]
            for inputName in providedInputs:
                # add any extra inputs to the module inputs
                if inputName not in moduleInputs:
                    # print a warning that an input was used that was
                    # not provided
                    print(f"WARNING: input {inputName} in include but not in {programName} itom")
                    moduleInputs[inputName] = providedInputs[inputName]

            from programExecutor import ProgramExecutor

            #
            # IN THIS LOCATION, FIGURE OUT WHAT DATA TYPE TO ASK FOR
            #
            executor = ProgramExecutor(self.programDirectory)
            includedModuleReturnTypes = executor.getVisualReturnTypesForProgram(program)
            if len(includedModuleReturnTypes) == 0:
                raise ValueError(f"ERROR: included program {programName} cannot return any of the includable types: {self.getIncludableTypes()}")
            

            targetReturnType = includedModuleReturnTypes[0]
            programOutput = executor.executeProgram(programName, 
                                                    {"startTimestamp": time.time(), 
                                                    "inputs": moduleInputs}, 
                                                    targetReturnType,
                                                    config=config)
            if not programOutput.succeeded():
                return dict(error="ERROR: program " + programName + " failed with message: " + programOutput.errorMessage(),
                            succeeded=False)
            else:
                # Convert the visual output to the target return type as needed
                visualStringRepr = None
                if targetReturnType == "html" or targetReturnType == "md":
                    visualStringRepr = str(programOutput.viz())
                elif targetReturnType == "png":
                    # Convert PNG bytes to base64 encoded HTML image
                    visualStringRepr = f'<img src="data:image/png;base64,{base64.b64encode(programOutput.viz()).decode("utf-8")}" />'
                else:
                    raise ValueError(f"ERROR: included program {programName} cannot return type: {targetReturnType}")

                if config.get("highlightIncludes", False):
                    # Create a tab with program name and any relevant metadata
                    # Build tab text with input parameters
                    inputParams = [f"{k}={v}" for k, v in moduleInputs.items()]
                    inputParamsStr = ", ".join(inputParams)

                    dataOutputs = [f"{k}={v}" for k, v in programOutput.data().items()]
                    dataOutputsStr = ", ".join(dataOutputs)

                    tabText = f'{programName} ({inputParamsStr}): ({dataOutputsStr})'

                    # Make the program name clickable by wrapping it in an anchor tag
                    # Add target="_top" to make the link open in the top-level browser window
                    tabText = f'<a href="/view/{programName}" target="_top" style="color: white; text-decoration: none;">{tabText}</a>'

                    tabContent = f'<div style="display: inline-block; background-color: red; color: white; padding: 2px 8px; border-radius: 4px 4px 0 0; margin-left: 10px; font-size: 0.8em; font-family: sans-serif;">{tabText}</div>'
                    visualStringRepr = f'{tabContent}<div style="border: 3px solid red; padding: 10px; margin: 0 0 10px 0;">{visualStringRepr}</div>'

                return dict(data=programOutput.data(),
                            visual=visualStringRepr,
                            succeeded=True)

        # Register the new functions
        env.globals["include"] = includeFn
        env.globals["return"] = return_variable
        env.globals["macros"] = env.from_string(macroText).module

        # Register the input variables
        for inputName, v in inputState.items():
            env.globals[inputName] = v

        # Render the template
        template = env.from_string(code)
        outputText = template.render()
        return outputText, outputState


class BasicDSLProcessor(PreprocessedDSL):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__(programDirectory)

    def getVisualReturnTypes(self) -> List[str]:
        return ["html", "png", "md"]
    
    def getIncludableTypes(self) -> List[str]:
        return ["html", "png", "md"]

    # The semantics of this DSL are as follows:
    # 1. Every module is purely functional
    # 2. Every module returns (1) a structured result, and (2) a visua result that can be rendered onscreen, (3) success or error code
    # 3. There is no interesting runtime state. A module runs to completion. If the module code changes, the module should be re-run.
    # 4. There is no interesting interactivity. All interactivity is at the interface level and anything permanent is a code change.
    #    (That is to say, there is no database or other form of state)
    # 5. Every module should be able to run to partial completion. An error does not bring it to a halt, but just makes the output worse
    def postprocess(self, processedCode: str, processedOutputState: dict, input: dict, outputNames: List[str], preferredVisualReturnType: str, config:dict) -> ProgramOutput:
        css = """<style>
            body {
                margin: 0;
            }
            h1, p {
                margin: 0.25em 0;
            }
            .panel {
                background-color: rgb(229,228,228);
                border-radius: 12px;
                padding: 1em;
                margin: 1em 0;
                box-shadow: 0 3px 9px rgba(0,0,0,0.08);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.2;
            }
            </style>
"""
        def render_markdown_in_divs(source: str) -> str:
            soup = BeautifulSoup(source, "html.parser")

            def process_node(node):
                for child in node.find_all("div"):
                    # Get the raw inner HTML/text of the div
                    inner_html = "".join(str(c) for c in child.contents).strip()
                    # Run it through the Markdown processor
                    rendered = mdlib.markdown(inner_html, extensions=["extra"])
                    # Replace contents of <div> with rendered HTML
                    child.clear()
                    if len(rendered) > 0:
                        child.append(BeautifulSoup(rendered, "html.parser"))
                    # Recursively process nested divs (if any)
                    process_node(child)

            process_node(soup)
            return str(soup)

        visualOutput = render_markdown_in_divs(processedCode)
        visualOutput = mdlib.markdown(visualOutput)
        html = css + visualOutput

        if preferredVisualReturnType == "html":
            return ProgramOutput(time.time(), "html", html, processedOutputState)
        elif preferredVisualReturnType == "md":
            return ProgramOutput(time.time(), "md", processedCode, processedOutputState)
        elif preferredVisualReturnType == "png":
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html)
                png_bytes = page.screenshot(full_page=True, type="png")
                browser.close()
                return ProgramOutput(time.time(), "png", png_bytes, processedOutputState)
        else:
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")

