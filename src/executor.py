#! /usr/bin/env python3
import sys
import os
import argparse
import json
import shutil
from programs import ProgramInput, ProgramOutput, ProgramDirectory, NamedProgram
from dslProcessor import ProgramExecutor
from typing import Optional, List, Tuple

if __name__ == "__main__":
    # process the command line, with help etc.
    # The user can either run a program by name (-run), or add a new program ()
    # Use a standard argparse for this
    parser = argparse.ArgumentParser(description="Execute a program")
    parser.add_argument("-run", type=str, help="The name of the program to execute")
    parser.add_argument("-add", type=str, help="The name of the program to add")
    parser.add_argument("-dsl", type=str, help="The DSL type for the program being added")
    parser.add_argument("-source", type=str, help="The source file for the program being added") 
    parser.add_argument("-refresh", action="store_true", help="Refresh the program directory")
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
        programName = args.run
        namedProgram = programDirectory.getProgram(programName)
        print(f"Executing program {namedProgram.name}")
        if not args.output:
            args.output = f"{namedProgram.name}.{args.format}"

        print(f"Outputting to {args.output}")
        print(f"Format: {args.format}")
        programOutput = programExecutor.executeProgram(namedProgram.name, ProgramInput(startTimestamp=0, inputs={}), preferredVisualReturnType=args.format)

        # Write the visual png to a file
        with open(args.output, "wb") as f:
            f.write(programOutput["visualOutput"])
    elif args.refresh:
        programDirectory.saveAndRefresh()
    elif args.add:
        if not args.dsl or not args.source:
            print("Error: Both -dsl and -source are required when adding a program")
            sys.exit(1)

        programName = args.add
        programFile = args.source
        programDirectory.addNewProgram(programName, f"Loaded from file {programFile}", args.dsl, [], open(programFile).read())
    else:
        print("Usage: python executor.py -run <program_name> or python executor.py -add <program_name>")
        sys.exit(1)


# DSL #2: VegaLite plus variables, and object inclusions

