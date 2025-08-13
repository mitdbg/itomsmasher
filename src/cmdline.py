#! /usr/bin/env python3
import sys
import os
import argparse
import json
import shutil
from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram, TracerNode
from programExecutor import ProgramExecutor
from typing import Optional, List, Tuple
import hashlib

def runProgram(programDirectory: ProgramDirectory, programExecutor: ProgramExecutor, programName: str, preferredVisualReturnType: str, config: dict, trace: bool):
    
    namedProgram = programDirectory.getProgram(programName)
    print(f"Executing program {namedProgram.name}")
    print(f"Outputting to {args.output}")
    print(f"Format: {args.format}")

    #print(f"Config: {namedProgram.config}")
    input = ProgramInput(startTimestamp=0, inputs={})
    root = None
    if args.trace:
        root = TracerNode(None)
    programOutput = programExecutor.executeProgram(namedProgram.name, input, preferredVisualReturnType=args.format, config=namedProgram.config,parentTracer=root)

    # Write the visual png to a file
    if args.format == "png":
        with open(args.output, "wb") as f:
            f.write(programOutput.viz())
    elif args.format == "html":
        with open(args.output, "w") as f:
            f.write(programOutput.viz())
    elif args.format == "md":
        with open(args.output, "w") as f:
            f.write(programOutput.viz())
    elif args.format == "mp4":
        with open(args.output, "wb") as f:
            f.write(programOutput.viz())
    else:
        raise ValueError(f"Invalid format: {args.format}")
    
    # Print the trace
    if args.trace:
        # pretty print the trace
        pretty = json.dumps(root.toJSON(), indent=4)
        print(pretty)
    return(root)

def status(programDirectory: ProgramDirectory):
    programs = programDirectory.getPrograms()
    print(f"Number of available programs: {len(programs)}")
    for i, program in enumerate(programs):
        print(f"{i+1}. {program.name}: {program.description}")


def parseExtraInputs(inputs: List[str]) -> dict:
    extraInputs = {}
    if (inputs is not None):
        for input in inputs:
            try:
                key, value = input.split("=")
                key = key.strip()
                value = value.strip()
                if (key == "" or value == ""):
                    print(f"Invalid input: {input}")
                    sys.exit(1)
                # determine if the value is a number, boolean, or string
                if (value.isdigit()):
                    value = int(value)
                elif (value.lower() == "true"):
                    value = True
                elif (value.lower() == "false"):
                    value = False
                else:
                    # check if it's a list or dictionary, otherwise assume it's a string
                    if (value.startswith("[") and value.endswith("]")):
                        value = json.loads(value)
                    elif (value.startswith("{") and value.endswith("}")):
                        value = json.loads(value)
                    else:
                        # wrap in quotes if it's a string
                        if (value.startswith("'") and value.endswith("'")):
                            value = f'"{value}"'
                        else:
                            value = value
                extraInputs[key] = value
                print(f"{key}: {value}")
            except ValueError:
                print(f"Invalid input: {input}")
                sys.exit(1)
    return extraInputs


if __name__ == "__main__":
    # process the command line, with help etc.
    # The user can either run a program by name (-run), or add a new program ()
    # Use a standard argparse for this
    parser = argparse.ArgumentParser(description="Execute a program")
    parser.add_argument("-run", type=str, help="The name of the program to execute")
    # -add can accept multiple file paths, separated by spaces on the commandline 
    parser.add_argument("-add", type=str, help="Source file of the program to add", nargs="+")
    parser.add_argument("-status", action="store_true", help="List all programs")
    parser.add_argument("-format", type=str, help="Preferred output format (png, html, etc)", default="png")
    parser.add_argument("-output", type=str, help="Output file path")
    parser.add_argument("-curry",type=str,help="Curry a program with a given input to create a new itom")
    parser.add_argument("-inputs",type=str,help="Inputs to curry or invoke in run mode",nargs="+")
    parser.add_argument("-r", "--recursive", action="store_true", help="Used with -add to try to recursively add all included itoms")
    parser.add_argument("-t", "--trace", action="store_true", help="Used with -run to print the trace")
    parser.add_argument("-i", "--includes", type=str, help="find the includes in an itom")

    args = parser.parse_args()

    extraInputs = parseExtraInputs(args.inputs)

    localProgramDir = ".programs"
    if not os.path.exists(localProgramDir):
        os.makedirs(localProgramDir)

    # Load and refresh the program directory
    programDirectory = ProgramDirectory(localProgramDir)
    programExecutor = ProgramExecutor(programDirectory)
    
    if args.run:
        if not args.output or not args.format:
            print("Error: -output and -format are required when running a program")
            sys.exit(1)
        programName = args.run
        runProgram(programDirectory, programExecutor, programName, args.format, args.output, args.trace)
    elif args.status:
        status(programDirectory)
    elif args.add:
        recursive = False
        if args.recursive:
            print("Recursively adding doesn't work yet")
            recursive = True
        # ITerate through the multiple files provided at -add
        for programFile in args.add:
            programName = programFile.split("/")[-1].split(".")[0]
            programDirectory.addNewProgram(programName, f"Loaded from file {programFile}", open(programFile).read(), refresh=True)
    elif args.curry:
        # Curry a program with a given input to create a new itom
        programName = args.curry
        # if extra inputs is empty or None, load the program
        # and print the inputs
        if extraInputs is None or len(extraInputs) == 0:
            program = programDirectory.getProgram(programName)
            print(f"Program {programName} inputs:")
            for key, value in program.inputs.items():
                print(f"\t{key}: {value}")
            sys.exit(1)
        else:
            if args.output is None:
                # generate the suffix as the md5 of the extra inputs
                suffix = hashlib.md5(json.dumps(extraInputs).encode()).hexdigest()
                args.output = f"{programName}_{suffix}"
            programDirectory.curryProgram(programName, extraInputs,args.output)
    elif args.includes:
        programName = args.includes
        program = programDirectory.getProgram(programName)
        processor = programExecutor.getDSLProcessor(program.dslId)
        tree = processor.getIncludes(program)
        # format the json using json.dumps
        print(tree)
    else:
        print("Usage: python cmdline.py -run <program_name> or python cmdline.py -add <program_name> or python cmdline.py -status")
        sys.exit(1)


# DSL #2: VegaLite plus variables, and object inclusions

