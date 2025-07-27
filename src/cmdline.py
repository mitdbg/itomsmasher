#! /usr/bin/env python3
import sys
import os
import argparse
import json
import shutil
from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram, TracerNode
from programExecutor import ProgramExecutor
from typing import Optional, List, Tuple

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
    #print(root.to_json())
    if args.trace:
        # pretty print the trace
        pretty = json.dumps(root.to_json(), indent=4)
        print(pretty)
    return(root)

def status(programDirectory: ProgramDirectory):
    programs = programDirectory.getPrograms()
    print(f"Number of available programs: {len(programs)}")
    for i, program in enumerate(programs):
        print(f"{i+1}. {program.name}: {program.description}")

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
    parser.add_argument("-output", type=str, help="Output file path for visual rendering")
    parser.add_argument("-r", "--recursive", action="store_true", help="Used with -add to try to recursively add all included itoms")
    parser.add_argument("-t", "--trace", action="store_true", help="Used with -run to print the trace")

    args = parser.parse_args()

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
            print("Recursively adding all included itoms")
            recursive = True
        # ITerate through the multiple files provided at -add
        for programFile in args.add:
            programName = programFile.split("/")[-1].split(".")[0]
            programDirectory.addNewProgram(programName, f"Loaded from file {programFile}", open(programFile).read(), refresh=True)
    else:
        print("Usage: python cmdline.py -run <program_name> or python cmdline.py -add <program_name> or python cmdline.py -status")
        sys.exit(1)


# DSL #2: VegaLite plus variables, and object inclusions

