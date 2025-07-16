#! /usr/bin/env python3
import sys
import os
import argparse
import json
import shutil
from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
from programExecutor import ProgramExecutor
from typing import Optional, List, Tuple

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
        namedProgram = programDirectory.getProgram(programName)
        print(f"Executing program {namedProgram.name}")
        print(f"Outputting to {args.output}")
        print(f"Format: {args.format}")

        programOutput = programExecutor.executeProgram(namedProgram.name, ProgramInput(startTimestamp=0, inputs={}), preferredVisualReturnType=args.format)

        # Write the visual png to a file
        if args.format == "png":
            with open(args.output, "wb") as f:
                f.write(programOutput.viz())
        elif args.format == "html":
            with open(args.output, "w") as f:
                f.write(programOutput.viz())
        else:
            raise ValueError(f"Invalid format: {args.format}")
    elif args.status:
        # Prefix with counter
        programs = programDirectory.getPrograms()
        print(f"Number of available programs: {len(programs)}")

        for i, program in enumerate(programDirectory.getPrograms()):
            print(f"{i+1}. {program.name}: {program.description}")
    elif args.add:
        # ITerate through the multiple files provided at -add
        for programFile in args.add:
            programName = programFile.split("/")[-1].split(".")[0]
            programDirectory.addNewProgram(programName, f"Loaded from file {programFile}", open(programFile).read(), refresh=True)
    else:
        print("Usage: python executor.py -run <program_name> or python executor.py -add <program_name> or python executor.py -status")
        sys.exit(1)


# DSL #2: VegaLite plus variables, and object inclusions

