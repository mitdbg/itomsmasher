import yaml
import io
import json
from typing import List
import sys

class ItomHeader:
    def __init__(self):
        self.description = None
        self.dslId = None
        self.inputs = {}
        self.outputs = {}
        self.config = {}
        self.remainingCode = ""

    def getRemainingCode(self) -> str:
        return self.remainingCode
    
    def setDescription(self, description) -> "ItomHeader":
        self.description = str(description)
        return self
    
    def setDslId(self, dslId) -> "ItomHeader":
        self.dslId = str(dslId) 
        return self
    
    def setInputs(self, value) -> "ItomHeader":
        # if input is not a dict, list or set, encapsulate it in a list
        if not isinstance(value, dict) and not isinstance(value, list) and not isinstance(value, set):
            value = [value]
        self.inputs = value
        return self
    
    def setOutputs(self, value) -> "ItomHeader":
        # if output is not a dict, list or set, encapsulate it in a list
        if not isinstance(value, dict) and not isinstance(value, list) and not isinstance(value, set):
            value = [value]
        self.outputs = value
        return self
    
    def setConfig(self, value) -> "ItomHeader":
        # if config is not a dict, list or set, encapsulate it in a list
        if not isinstance(value, dict) and not isinstance(value, list) and not isinstance(value, set):
            value = [value]
        self.config = value
        return self
    
    def getDescription(self,default:str = "") -> str:
        return self.description if self.description is not None else default
    
    def getDslId(self,default:str = "") -> str:
        return self.dslId if self.dslId is not None else default
    
    def getInputs(self,default:dict = {}) -> dict:
        return self.inputs if self.inputs is not None else default
    
    def getOutputs(self,default:dict = {}) -> dict:
        return self.outputs if self.outputs is not None else default
    
    def getConfig(self,default:dict = {}) -> dict:
        return self.config if self.config is not None else default
    
    
    def parseFromItomFile(self, filename: str) -> "ItomHeader":
        # Extract header lines
        with open(filename, "r") as f:
            code = f.read()

        return self.parseFromItomString(code)

    def parseFromItomString(self, code: str) -> "ItomHeader":
        header_lines = []
        code_lines = []
        in_header = True
    
        for line in code.split("\n"):
            if in_header and line.startswith("#@"):
                # Remove #@ prefix and append to header
                header_lines.append(line[2:].rstrip())
            else:
                in_header = False
                code_lines.append(line)

        self.remainingCode = "\n".join(code_lines)

        return self.parse(header_lines)
        
    def parse(self, header_lines: List[str]) -> "ItomHeader":
        # Parse header as YAML
   
        try:
            header_yaml = yaml.safe_load(io.StringIO("\n".join(header_lines)))
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in header: {str(e)}")

        if not isinstance(header_yaml, dict):
            raise ValueError("Header YAML must be a dictionary/mapping")
        
        
        # Extract required fields
        self.description = header_yaml.get("description", "")
        self.dslId = header_yaml.get("dsl")
        self.inputs = header_yaml.get("inputs", {})
        self.outputs = header_yaml.get("outputs", {})
        self.config = header_yaml.get("config", {})

        return self

    def processVariables(self, variables) -> str:

        #print(variables)
        indent = 3
        toRet = ""
        if isinstance(variables, set) or isinstance(variables, list):
            for key in variables:
                toRet += "#@" + " " * indent + "- " + key + "\n"
        # if it's a dict
        elif isinstance(variables, dict):
            for key, value in variables.items():
                # look at the type of the value
                if isinstance(value, set) or isinstance(value, list):
                    # do something
                    toRet += "#@" + " " * (indent) + "- " + value + "\n"
                    for item in value:
                        toRet += "#@" + " " * (indent + 2) + "- " + str(item) + "\n"
                elif isinstance(value, dict):
                    # do something
                    toRet += "#@" + " " * (indent) + key + ":\n"
                    for key2, value2 in value.items():
                        toRet += "#@" + " " * (indent+2) + key2 + ": " + str(value2) + "\n"
                else:
                    toRet += "#@" + " " * (indent) + key + ": " + str(value) + "\n"
        else:
            toRet += "#@" + " " * indent + str(variables) + "\n"
        
        return toRet

    def toJSON(self) -> str:
        return {
            "description": self.description,
            "dslId": self.dslId,
            "inputs": self.inputs if len(self.inputs) > 0 else None,
            "outputs": self.outputs if len(self.outputs) > 0 else None,
            "config": self.config if len(self.config) > 0 else None
        }
    
    # convert to header string
    def __str__(self):
        # add a #@ prefix to each line
        toRet = ""
        if self.dslId != None:
            toRet += "#@ dsl: " + self.dslId + "\n"
        else:
            toRet += "#@ dsl: ???\n"

        if self.description != None:
                toRet += "#@ description: " + self.description + "\n"
        # check if self.inputs is not empty
        if self.inputs != {}:
            toRet += "#@ inputs:\n"
            toRet += self.processVariables(self.inputs)
        if self.outputs != {}:
            toRet += "#@ outputs:\n"
            toRet += self.processVariables(self.outputs)
        if self.config != {}:
            toRet += "#@ config:\n"
            toRet += self.processVariables(self.config)
        return toRet
    
# main, read from a file name
if __name__ == "__main__":
    header = ItomHeader()
    header.parseFromItomFile(sys.argv[1])
    print(header)

    test = ItomHeader()
    test.setDslId("test")
    test.setInputs(["test","test2"])
    test.setOutputs({"test":"test2","test3":{'a':'b'}})
    test.setConfig({"test3":"test4"})
    print(test)