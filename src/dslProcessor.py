from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
import time, os, base64
import re
from typing import Optional, List, Tuple, Any
import markdown as mdlib
import copy

# DSLProcessor is a generic superclass for all DSL processors
class DSLProcessor:
    def __init__(self):
        pass

    def getVisualReturnTypes(self) -> List[str]:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")

    def runProgram(self, program: NamedProgram, input: ProgramInput, preferredVisualReturnType) -> ProgramOutput:
        # Create pair of input and empty output
        latestCode = program.codeVersions[-1]
        latestExecutionHistory = program.executions[-1]
        programOutput = self.process(latestCode, input["inputs"], program.outputs, preferredVisualReturnType)
        latestExecutionHistory.append((input, programOutput))
        return programOutput


class Model2DSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def getVisualReturnTypes(self) -> List[str]:
        return ["html"]

    # The semantics of this DSL are as follows:
    # 1. Every module is purely functional
    # 2. Every module returns (1) a structured result, and (2) a visua result that can be rendered onscreen, (3) success or error code
    # 3. There is no interesting runtime state. A module runs to completion. If the module code changes, the module should be re-run.
    # 4. There is no interesting interactivity. All interactivity is at the interface level and anything permanent is a code change.
    #    (That is to say, there is no database or other form of state)
    # 5. Every module should be able to run to partial completion. An error does not bring it to a halt, but just makes the output worse
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        return self.jinjaProcess(code, input, preferredVisualReturnType)
    
    def jinjaProcess(self, code: str, input: dict, preferredVisualReturnType: str) -> ProgramOutput:
        # Use Jinja to process the document
        from jinja2 import Environment, BaseLoader, pass_context

        outputState = {}
        inputState = copy.deepcopy(input)
        env = Environment(loader=BaseLoader)

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
            for inputName in program.inputs:
                if inputName not in providedInputs:
                    return dict(error="ERROR: includeFn could not find input: " + inputName,
                                succeeded=False)
                moduleInputs[inputName] = providedInputs[inputName]

            from programExecutor import ProgramExecutor
            programOutput = ProgramExecutor(self.programDirectory).executeProgram(programName, 
                                                                                  {"startTimestamp": time.time(), 
                                                                                   "inputs": moduleInputs}, 
                                                                                   preferredVisualReturnType)
            if not programOutput.succeeded():
                return dict(error="ERROR: program " + programName + " failed with message: " + programOutput.errorMessage(),
                            succeeded=False)
            else:
                return dict(data=programOutput.data(),
                            visual=str(programOutput.viz()),
                            succeeded=True)

        env.globals["include"] = includeFn
        env.globals["return"] = return_variable
        for inputName, v in inputState.items():
            env.globals[inputName] = v

        template = env.from_string(code)
        outputText = template.render()
        visualOutput = mdlib.markdown(outputText)
        return ProgramOutput(time.time(), "html", visualOutput, outputState)



class EscapedSublanguageDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory

    def __convertToLocalDSL__(self, data: Any) -> str:
        raise NotImplementedError("DSLProcessor is an abstract class and cannot be instantiated directly")



    def __preprocess__(self, code: str, input: dict, preferredVisualType: Optional[str] = None, startBlock: Optional[str] = "{{", endBlock: Optional[str] = "}}") -> Tuple[str, dict]:
        # Any part of the code in double-braces should be replaced with a pre-processed version of the code
        # Let's start by iterating through the code and finding all double-brace blocks
        # We'll replace each double-brace block with the pre-processed version of the code
        # We'll return the pre-processed code

        # initialize variables with contents of input (but make a copy)
        variables = input.copy()

        # PART 1.  Prepreocess brace inserts.  Assignments, variable accesses, and includes.
        def processElement(code_block: str, variables: dict) -> Any:

            # Pattern to match include(programName) or include(programName, key1=val1, key2=val2, ...)
            # Program name can be quoted or unquoted
            # Key-value pairs are optional
            includePattern = re.compile(
                r"""include\(
                    \s*
                    (?P<progname>
                        (?:"[^"]*"|'[^']*')  # Quoted string
                        |
                        [a-zA-Z_]\w*         # Unquoted variable name
                    )
                    \s*
                    (?:,
                        \s*
                        (?P<params>
                            [a-zA-Z_]\w*    # key
                            \s*=\s*
                            (?:[a-zA-Z_]\w* | "[^"]*" | '[^']*' | \d+)  # value
                            (?:\s*,\s*[a-zA-Z_]\w*\s*=\s*(?:[a-zA-Z_]\w* | "[^"]*" | '[^']*' | \d+))*  # more k=v
                        )
                    )?
                    \s*
                    \)""",
                re.VERBOSE
            )

            # Check if the code block is a variable assignment of the form varname = value. Use regex to match this.
            # It's OK if there is no whitespace before or after the equals sign
            if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*[ \t]*=[ \t]*.*$", code_block):
                # It's a variable assignment
                # Split the code block into lhs and rhs using the leftmost equals sign
                lhs, rhs = code_block.split("=", 1)
                lhs = lhs.strip()
                rhs = rhs.strip()

                rhsProcessed = processElement(rhs, variables)
                variables[lhs] = rhsProcessed
                return None
            
            # Check if the code block has a dotted field access. Must have at least one dot.
            elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$", code_block):
                # It's a variable access
                # Split the code block into varName and then remainder (of zero or more dotted names)
                lhs, rhs = code_block.split(".", 1)
                val = variables[lhs]
                parts = rhs.split(".")

                for part in parts:
                    if isinstance(val, ProgramOutput):
                        if part == "data":
                            val = val.data()
                        else:
                            raise ValueError(f"Invalid field: {part} for program output")
                    elif isinstance(val, dict):
                        val = val[part]
                    else:
                        raise ValueError(f"Invalid dotted field access: {code_block}")

                return val

            # Check if the code block matches the include pattern
            elif includePattern.match(code_block):
                # It's an include statement
                # Form of include is 'include(programName, input0=value0, input1=value1, input2=value2)' or 'include(programName)'
                # where programName is a quoted string or a variable name.
                # The comma-separated list gives named parameter pairs
                match = includePattern.fullmatch(code_block)
                programName = match.group("progname")

                if programName.startswith("\"") and programName.endswith("\""):
                    programName = programName.strip("\"")
                else:
                    programName = processElement(programName, variables)

                # Iterate through the matched parameters
                # Handle case where there are no parameters
                paramList = match.group("params")
                if paramList is None:
                    paramList = []
                else:
                    paramList = paramList.split(",")

                # strip whitespace from all params
                paramList = [p.strip() for p in paramList]
                # parse the param list into a dictionary
                paramDict = {}
                for p in paramList:
                    key, value = p.split("=")
                    key = key.strip()
                    value = value.strip()
                    paramDict[key] = value
                includedProgramName = programName.strip("\"'")
                processedParamDict = {k: processElement(v, variables) for k, v in paramDict.items()}
                inputData = {"startTimestamp": time.time(), "inputs": processedParamDict}
                from programExecutor import ProgramExecutor
                return ProgramExecutor(self.programDirectory).executeProgram(includedProgramName, inputData, preferredVisualType, inferInputs=True, callingProgramContext=code)
            
            # Check if it's a bracketed field access of the form x[y]
            elif re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\[[a-zA-Z_][a-zA-Z0-9_]*\]$", code_block):
                # It's a bracketed field access
                # Split the code block into varName and then remainder (of zero or more dotted names)
                lhs, rhs = code_block.split("[", 1)
                lhs = lhs.strip()
                rhs = rhs.strip("]")

                val = variables[lhs]
                rhsSide = processElement(rhs, variables)
                if isinstance(val, ProgramOutput):
                    return val.data()[rhsSide]
                else:
                    return val[rhsSide]
            else:
                # It's a value. Either a variable name or a literal value.
                if code_block in variables:
                    return variables[code_block]
                else:
                    # It's a literal value. Parse like a Python atomic literal
                    if code_block == "":
                        return ""
                    else:
                        test = str(eval(code_block))
                        return test

        while startBlock in code:
            start = code.find(startBlock)
            end = code.find(endBlock)
            if start == -1 or end == -1:
                break
            # Get the code between the double-braces
            code_block = code[start+2:end]
            # Replace the double-brace block with the sublanguage-processed version of the code
            code = code[:start] + self.__convertToLocalDSL__(processElement(code_block, variables)) + code[end+2:]

        # Process the code to handle structures of the following form:
        # ::grid rows=2 cols=3
        # [cell] Welcome to the dashboard!
        # [cell span=2] [Plot id="vis1"]
        # [cell align=center valign=middle bgcolor=#f0f0f0] [Button text="Run"]
        # [cell colspan=3] [TextBox name="notes" rows=4]
        # ::endgrid
        #

        # PART 2.  Parse the DSL blocks (grid and panel)
        def parse_grid_block(header_line, lines):
            grid_meta = {}
            header_match = re.match(r"::grid\s+(.*)", header_line)
            if header_match:
                grid_meta = dict(re.findall(r'(\w+)=([^\s]+)', header_match.group(1)))

            cells = []
            cellContents = None
            cellAttrs = None
            for line in lines:
                line = line.strip()
                if len(line) == 0:
                    continue
                if line.startswith('[cell'):
                    if cellContents is not None:
                        cells.append((cellContents.strip(), cellAttrs))
                        cellContents = None
                        cellAttrs = None

                    attr_match = re.match(r'\[cell([^\]]*)\](.*)', line)
                    if not attr_match:
                        continue
                    attr_str, content = attr_match.groups()
                    attrs = dict(re.findall(r'(\w+)=(".*?"|\S+)', attr_str))
                    attrs = {k: v.strip('"') for k, v in attrs.items()}
                    cellAttrs = attrs
                    cellContents = content.strip()
                else:
                    if cellContents is None:
                        raise ValueError("Must start a cell with [cell]")
                    cellContents += "\n" + line

            if cellContents is not None:
                cells.append((cellContents.strip(), cellAttrs))

            return grid_meta, cells

        # MARKDOWN RENDERING
        def render_markdown(content):
            return mdlib.markdown(content.strip(), extensions=["extra"])

        # GRID HANDLING, called when a grid block is closed.
        def render_grid_as_html(grid_meta, cells):
            cols = int(grid_meta.get("cols", "1"))

            html = []
            html.append(f'<div class="grid" style="display: grid; grid-template-columns: repeat({cols}, 1fr); gap: 0.25em;">')

            for content, attrs in cells:
                span = int(attrs.get("span", attrs.get("colspan", "1")))
                align = attrs.get("align", "left")
                valign = attrs.get("valign", "top")

                # Map valign to corresponding CSS flex alignment
                valign_map = {
                    "top": "flex-start",
                    "middle": "center",
                    "bottom": "flex-end"
                }
                flex_align = valign_map.get(valign, "flex-start")  # default to top

                styles = [
                    f"grid-column: span {span};",
                    f"display: flex;",
                    f"align-items: {flex_align};",
                    f"justify-content: {align if align in ['flex-start', 'center', 'flex-end'] else 'center'};",
                    f"text-align: {align};"
                ]

                if "bgcolor" in attrs:
                    styles.append(f"background-color: {attrs['bgcolor']};")

                renderedMd = render_markdown(content)
                style_attr = " ".join(styles)
                html.append(f'  <div class="cell" style="{style_attr}">{renderedMd}</div>')

            html.append('</div>')
            return "\n".join(html)

        # PANEL HANDLING, called when a panel block is closed.
        def render_panel_as_html(header, lines):
            # parse the header. It has the same form as grid header
            header_match = re.match(r"::panel\s+(.*)", header)
            if header_match:
                header_meta = dict(re.findall(r'(\w+)=([^\s]+)', header_match.group(1)))
            else:
                header_meta = {}

            classLabel = header_meta.get("class", "panel")
            renderedMd = render_markdown("\n" + "\n".join(lines))
            return f"<div class='{classLabel}'>{renderedMd}</div>"


        outputCode = []
        gridHeaders = []
        gridLines = []
        panelHeaders = []
        panelLines = []
        currentBlock = []

        for line in code.split("\n"):
            if line.strip().startswith("::grid"):
                currentBlock.append("grid")
                gridHeaders.append(line.strip())
                gridLines.append([])
            elif line.strip().startswith("::endgrid"):
                if currentBlock[-1] != "grid":
                    raise ValueError("::endgrid found without a corresponding ::grid")
                meta, cells = parse_grid_block(gridHeaders[-1], gridLines[-1])
                currentBlock.pop()
                gridLines.pop()
                gridHeaders.pop()
                html = render_grid_as_html(meta, cells)
                if len(currentBlock) > 0:
                    if currentBlock[-1] == "grid":
                        gridLines[-1].append(html)
                    elif currentBlock[-1] == "panel":
                        panelLines[-1].append(html)
                else:
                    outputCode.append(html)
            elif line.strip().startswith("::panel"):
                currentBlock.append("panel")
                panelHeaders.append(line.strip())
                panelLines.append([])
            elif line.strip().startswith("::endpanel"):
                if currentBlock[-1] != "panel":
                    raise ValueError("::endpanel found without a corresponding ::panel")
                html = render_panel_as_html(panelHeaders[-1], panelLines[-1])
                currentBlock.pop()
                panelLines.pop()
                panelHeaders.pop()
                if len(currentBlock) > 0:
                    if currentBlock[-1] == "grid":
                        gridLines[-1].append(html)
                    elif currentBlock[-1] == "panel":
                        panelLines[-1].append(html)
                else:
                    outputCode.append(html)
            elif len(currentBlock) > 0 and currentBlock[-1] == "grid":
                gridLines[-1].append(line.strip())
            elif len(currentBlock) > 0 and currentBlock[-1] == "panel":
                panelLines[-1].append(line.strip())
            else:
                outputCode.append(line.strip())

        code = "\n".join(outputCode)

        return code, variables

    def __postProcess__(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        raise NotImplementedError("EscapedSublanguageDSLProcessor is an abstract class and cannot be instantiated directly")

    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        # Preprocess the document
        preprocessedSourceCode, finalVariables = self.__preprocess__(code, input, preferredVisualReturnType)
        return self.__postProcess__(preprocessedSourceCode, finalVariables, outputNames, preferredVisualReturnType)

