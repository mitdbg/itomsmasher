#! /usr/bin/env python3
## DSLProcessor is a class that processes a DSL string and returns a string.
## NamedProgram is a class that represents a program with a name, description, DSL ID, code versions, inputs, and outputs.
import sys
import json
from dslProcessor import BasicDSLProcessor
from programs import ProgramInput, ProgramOutput
from typing import Optional, List, Tuple

