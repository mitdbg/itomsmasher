import sys
import json
import os
from datetime import datetime
from typing import Optional, List, Tuple, TypedDict, Any
from ItomHeader import ItomHeader
import re

# ProgramInput is a class that represents the input of a program
class ProgramInput(TypedDict):
    startTimestamp: int
    inputs: TypedDict

# ProgramOutput is a class that represents the output of a program
class ProgramOutput:
    def __init__(self, endTimestamp: int, visualReturnType: str, visualOutput: Any, dataOutputs: TypedDict, succeeded: bool=True, errorMessage: str=""):
        self.__endTimestamp = endTimestamp
        self.__visualReturnType = visualReturnType
        self.__visualOutput = visualOutput
        self.__dataOutputs = dataOutputs
        self.__succeeded = succeeded
        self.__errorMessage = errorMessage

    def endTimestamp(self) -> int:
        return self.__endTimestamp
    
    def viz(self) -> Any:
        return self.__visualOutput
    
    def visualReturnType(self) -> str:
        return self.__visualReturnType
    
    def data(self) -> TypedDict:
        return self.__dataOutputs
    
    def succeeded(self) -> bool:
        return self.__succeeded
    
    def errorMessage(self) -> str:
        return self.__errorMessage

# NamedProgram is a class that represents a program with a 
# name, description, DSL ID, code versions, inputs, and outputs.
class NamedProgram:
    def __init__(self, 
                 name: str, 
                 created: int,
                 modified: int,
                 description: str,
                 dslId: str,
                 inputs: dict[str, dict],
                 outputs: List[Tuple[str, dict]],
                 rawCodeVersions: List[str],
                 codeVersions: List[str],
                 executions: List[List[Tuple[ProgramInput, ProgramOutput]]],
                 config: dict):
        self.name = name
        self.created = created
        self.modified = modified
        self.description = description
        self.dslId = dslId
        self.inputs = inputs
        self.outputs = outputs
        self.rawCodeVersions = rawCodeVersions
        self.codeVersions = codeVersions
        self.executions = executions
        self.config = config

    def clone(self) -> "NamedProgram":
        return NamedProgram(self.name, 
                            self.created, 
                            self.modified, 
                            self.description, 
                            self.dslId, 
                            self.inputs.copy(), 
                            self.outputs.copy(), 
                            self.rawCodeVersions.copy(), 
                            self.codeVersions.copy(), 
                            self.executions.copy(), 
                            self.config.copy())
    
    def getHeader(self) -> ItomHeader:
        hdr = ItomHeader()
        hdr.setDescription(self.description)
        hdr.setDslId(self.dslId)
        hdr.setInputs(self.inputs)
        hdr.setOutputs(self.outputs)
        return hdr
    
    @classmethod
    def __processCodeHeader__(cls, code: str) -> Tuple[str, str, str, List[str], List[str], dict]:
        # Read the code header to get the description, dslId, inputs, and outputs.
        # The header is a list of #@-prefixed lines. Each line is a key-value pair of the form "key: value".
        # The header should be removed from the code text.
        # Once we hit a line that is not prefixed with #@, we stop parsing the header.

        
        # Parse header as YAML
        try:
            hdr = ItomHeader()
            hdr.parseFromItomString(code)
        except Exception as e:
            raise ValueError(f"Invalid header: {str(e)}")

        description = hdr.getDescription(default="")
        dslId = hdr.getDslId(default="")
        inputs = hdr.getInputs(default={})
        outputs = hdr.getOutputs(default={})
        config = hdr.getConfig(default={})

        remainingCode = hdr.getRemainingCode()
        if dslId is None or dslId == "":
            raise ValueError("No dsl field found in header")

        return remainingCode, description, dslId, inputs, outputs, config


    @classmethod
    def from_code(cls, name: str, rawCode: str) -> "NamedProgram":
        remainingCode, description, dslId, inputs, outputs, config = cls.__processCodeHeader__(rawCode)
        return cls(name, datetime.now(), datetime.now(), description, dslId, inputs, outputs, [rawCode], [remainingCode], [[]], config)

    # init from dict
    @classmethod
    def from_dict(cls, dict: dict) -> "NamedProgram":
        return cls(dict["name"],                    
                   datetime.fromisoformat(dict["created"]),
                   datetime.fromisoformat(dict["modified"]),
                   dict["description"], 
                   dict["dslId"], 
                   dict["inputs"],
                   dict["outputs"],
                   dict["rawCodeVersions"],
                   dict["codeVersions"],
                   dict["executions"],
                   dict["config"])

    # init from json
    @classmethod
    def from_json(cls, json_str: str) -> "NamedProgram":
        return cls.from_dict(json.loads(json_str))

    # save to json
    def toJson(self) -> str:
        return json.dumps({
            "name": self.name,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "description": self.description,
            "dslId": self.dslId,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "rawCodeVersions": self.rawCodeVersions,
            "codeVersions": self.codeVersions,
            "executions": self.executions,
            "config": self.config
        })

    def getLatestCode(self) -> str:
        return self.codeVersions[-1]
    
    def getLatestRawCode(self) -> str:
        return self.rawCodeVersions[-1]

    def getExecutionHistory(self) -> List[Tuple[ProgramInput, ProgramOutput]]:
        return self.executions[-1]

    def getLatestExecution(self) -> Tuple[ProgramInput, ProgramOutput]:
        return self.executions[-1][-1]

    def addCodeVersion(self, newRawCode: str, newCode: str) -> None:
        self.rawCodeVersions.append(newRawCode)
        self.codeVersions.append(newCode)
        self.executions.append([])
        self.modified = datetime.now()





# ProgramDirectory is a class that stores all the programs in the system
class ProgramDirectory:
    def __init__(self, localProgramDir: str):
        self.programs = {}
        self.localProgramDir = localProgramDir
        self.programExecutor = None

        # Each program has its own directory, so we need to list all the directories in the program directory
        for file in os.listdir(localProgramDir):
            if os.path.isdir(os.path.join(localProgramDir, file)):
                # Find json file in the directory
                jsonFile = os.path.join(localProgramDir, file, "program.json")
                if os.path.exists(jsonFile):
                    # Load the json file
                    with open(jsonFile, "r") as f:
                        program = NamedProgram.from_dict(json.load(f))
                        if program.name in self.programs:
                            raise ValueError(f"Program {program.name} already exists")
                        self.programs[program.name] = program

        self.__refresh__()

    def curryProgram(self, programName: str, extraInputs: dict, outputProgramName: str) -> None:
        program = self.programs[programName]
        # clone the program
        newProgram = program.clone()
        newProgram.name = outputProgramName
        # get the existing inputs
        existingInputs = program.inputs
        # iterate over the extra inputs
        for key, value in extraInputs.items():
            # get the value from existing input
            oldValue = existingInputs[key]
            # if it's a dictionary, replace the default
            if isinstance(oldValue, dict):
                newProgram.inputs[key]["default"] = value
            # if it's a list, replace the first element
            else:
                newProgram.inputs[key] = value

        # add the new program to the program directory
        self.addNewNamedProgram(newProgram)
       

    def save(self) -> None:
        for programName, program in self.programs.items():
            programDir = os.path.join(self.localProgramDir, programName)
            if not os.path.exists(programDir):
                os.makedirs(programDir)

            # Create the code file if it doesn't exist
            codeFile = os.path.join(programDir, "code.itom")
            if not os.path.exists(codeFile):
                with open(codeFile, "w") as f:
                    f.write(program.getLatestRawCode())

            # Write out the program JSON file
            with open(os.path.join(self.localProgramDir, programName, "program.json"), "w") as f:
                f.write(program.toJson())

    def __refresh__(self) -> None:
        changed = False
        for programName, program in self.programs.items():
            # Load the code file and update the program if it has changed
            programDir = os.path.join(self.localProgramDir, programName)
            with open(os.path.join(programDir, "code.itom"), "r") as f:
                rawCodeText = f.read()
                if rawCodeText != program.getLatestRawCode():
                    remainingCode, description, dslId, inputs, outputs,config = NamedProgram.__processCodeHeader__(rawCodeText)
                    program.addCodeVersion(rawCodeText, remainingCode)
                    program.description = description
                    program.dslId = dslId
                    program.inputs = inputs
                    program.outputs = outputs
                    program.config = config
                    changed = True
        if changed:
            self.save()

    def addNewNamedProgram(self,program:NamedProgram) -> None:
        # add the the program to the program directory
        self.programs[program.name] = program
        programName = program.name
        programDir = os.path.join(self.localProgramDir, programName)
        if not os.path.exists(programDir):
            os.makedirs(programDir)

        # Create the code file if it doesn't exist
        codeFile = os.path.join(programDir, "code.itom")
        code = program.getLatestRawCode()
        # remove all the #@ lines 
        code = re.sub(r'^#@.*\n', '', code, flags=re.MULTILINE)
        newCode = str(program.getHeader()) + "\n" + code
        with open(codeFile, "w") as f:
            f.write(newCode)

        # Write out the program JSON file
        with open(os.path.join(self.localProgramDir, programName, "program.json"), "w") as f:
            f.write(program.toJson())

    def addNewProgram(self, programName: str, metadataComment: str, rawCode: str, refresh: bool = False) -> None:
        if programName not in self.programs:
            print(f"Adding new program {programName}")
            program = NamedProgram.from_code(programName, rawCode)
            self.programs[program.name] = program
            self.save()
        else:
            if not refresh:
                raise ValueError(f"Program {programName} already exists")
            else:
                # Copy the new program source file (code.itom)to the program directory and refresh
                program = self.programs[programName]
                needToUpdate = False
                if program.getLatestRawCode() != rawCode:
                    needToUpdate = True

                if needToUpdate:
                    programDir = os.path.join(self.localProgramDir, programName)
                    if os.path.exists(programDir):
                        # Copy the new program source file (code.itom) to the program directory
                        with open(os.path.join(programDir, "code.itom"), "w") as f:
                            f.write(rawCode)

                    print(f"Updating program {programName}")
                    self.__refresh__()



    def getPrograms(self) -> List[NamedProgram]:
        return list(self.programs.values())

    def getProgram(self, programName: str) -> NamedProgram:
        if programName not in self.programs:
            raise ValueError(f"Program {programName} not found")
        return self.programs[programName]

    def setProgramExecutor(self, programExecutor: "ProgramExecutor") -> None:
        self.programExecutor = programExecutor

    def getProgramExecutor(self) -> "ProgramExecutor":
        return self.programExecutor
    
class ItomIncludeTree:
    def __init__(self, program:str, invokes:list["ItomIncludeTree"]=None, header:"ItomHeader"=None, parent=None, kwargs:dict={}):
        self.program = program
        self.invokes = invokes
        self.header = header
        self.parent = parent
        self.kwargs = kwargs

    def addInvokes(self, child: "ItomIncludeTree"):
        #print("addingChild from: ",[self]," to: ",[child])
        if self.invokes is None:
            self.invokes = [child]
        else:
            self.invokes.append(child)
        child.parent = self

    def getKwargs(self) -> dict:
        return self.kwargs
    
    def setKwargs(self, kwargs:dict):
        self.kwargs = kwargs
    
    def getParent(self) -> "ItomIncludeTree":
        return self.parent
    
    def getInvokes(self) -> list["ItomIncludeTree"]:
        return self.invokes
    
    def getProgram(self) -> str:
        return self.program
    
    def toJSON(self) -> dict:
        #print([self])
        #print(self.program,len(self.invokes))
        tInvokes = []
        if self.invokes is not None:
            for child in self.invokes:
                if self != child:
                    tInvokes.append(child.toJSON())
        return {
            "program": self.program,
            "kwargs":self.getKwargs() if len(self.getKwargs()) > 0 else None,
            "header": self.header.toJSON() if self.header is not None else None,
            "invokes": tInvokes          #  "invokes": [child.to_json() for child in self.getInvokes()],
        }
    
    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


class TracerNode:
    def __init__(self, program: 'NamedProgram', output: Optional['ProgramOutput'] = None, input: Optional['ProgramInput'] = None):
        self.program = program
        self.output = output
        self.input = input
        self.duration = None
        self.starttime = datetime.now()
        self.endtime = None
        self.children = []
    
    def toJSON(self) -> dict:
        if self.duration is None:
            self.end(None)
        return {
            "program": self.program.name if self.program is not None else "ROOT",
            "input": self.input if self.input is not None else None,
            "starttime": self.starttime.isoformat(),
            "output": {'data': self.output.data()} if self.output is not None else None,
            "endtime": self.endtime.isoformat() if self.endtime is not None else None,
            "duration": self.duration.total_seconds() if self.duration is not None else None,
            "children": [child.toJSON() for child in self.children]
        }

    def start(self, input: Optional['ProgramInput'] = None):
        self.starttime = datetime.now()
        if input is not None:
            self.input = input

    def end(self, output: Optional['ProgramOutput'] = None):
        self.endtime = datetime.now()
        self.duration = self.endtime - self.starttime
        
        if output is not None:
            self.output = output

    def addChild(self, child: 'TracerNode') -> 'TracerNode':
        self.children.append(child)
        return self

    def getChildren(self) -> List['TracerNode']:
        return self.children
    
    