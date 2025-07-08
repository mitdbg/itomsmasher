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
    parser.add_argument("-add", type=str, help="The name of the program file to add")
    args = parser.parse_args()

    localProgramDir = ".programs"
    if not os.path.exists(localProgramDir):
        os.makedirs(localProgramDir)

    # Load and refresh the program directory
    programDirectory = ProgramDirectory()

    # Each program has its own directory, so we need to list all the directories in the program directory
    for file in os.listdir(localProgramDir):
        if os.path.isdir(os.path.join(localProgramDir, file)) and file.endswith(".itom"):
            # Find json file in the directory
            jsonFile = os.path.join(localProgramDir, file, "program.json")
            if os.path.exists(jsonFile):
                # Load the json file
                with open(jsonFile, "r") as f:
                    program = NamedProgram.from_dict(json.load(f))

                    # Load the code file
                    codeFile = os.path.join(localProgramDir, file, "code.itom")
                    if os.path.exists(codeFile):
                        with open(codeFile, "r") as f:
                            codeText = f.read()
                            latestCode = program.getLatestCode()
                            if latestCode != codeText:
                                program.addCodeVersion(codeText)
                                # save the program JSON file
                                with open(jsonFile, "w") as f:
                                    f.write(program.toJson())

                    programDirectory.addProgram(program)
    programExecutor = ProgramExecutor(programDirectory)
    
    if args.run:
        programName = args.run
        namedProgram = programDirectory.getProgram(programName)
        print(f"Executing program {namedProgram.name}")
        programOutput = programExecutor.executeProgram(namedProgram.name, ProgramInput(startTimestamp=0, inputs={}), preferredVisualReturnType="png")

        # Write the visual png to a file
        with open(f"output.png", "wb") as f:
            f.write(programOutput["visualOutput"])
    elif args.add:
        programFile = args.add
        programName = programFile.split("/")[-1].split(".")[0]
        localProgramDir = os.path.join(localProgramDir, programName + ".itom")
        if not os.path.exists(localProgramDir):
            os.makedirs(localProgramDir)
            # Create the JSON file
            with open(os.path.join(localProgramDir, "program.json"), "w") as f:
                f.write(NamedProgram(programName, "Loaded from file {programFile}", "basic", []).toJson())

            # Create the code file
            with open(os.path.join(localProgramDir, "code.itom"), "w") as f:
                f.write(open(programFile).read())

            newProgram = NamedProgram.from_dict(json.loads(open(os.path.join(localProgramDir, "program.json")).read()))
            newProgram.addCodeVersion(open(os.path.join(localProgramDir, "code.itom")).read())
            with open(os.path.join(localProgramDir, "program.json"), "w") as f:
                f.write(newProgram.toJson())
            programDirectory.addProgram(newProgram)
        else:
            # Check if the new code is different from the old code. If so, copy it into place and update the program directory
            # First, load the old program
            with open(os.path.join(localProgramDir, "program.json"), "r") as f:
                oldProgram = NamedProgram.from_dict(json.load(f))

            # Then, load the new code
            with open(programFile, "r") as f:
                newCodeText = f.read()

            if (newCodeText != oldProgram.getLatestCode()):
                # Copy the code file into place
                shutil.copy(programFile, os.path.join(localProgramDir, "code.itom"))

                # Update the program directory
                oldProgram.addCodeVersion(newCodeText)
                with open(os.path.join(localProgramDir, "program.json"), "w") as f:
                    f.write(oldProgram.toJson())
    else:
        print("Usage: python executor.py -run <program_name> or python executor.py -add <program_name>")
        sys.exit(1)


# DSL #1: Markdown plus variables, and object inclusions
# # Welcome to the world of Bubble Sort
# ## The theory
# We want to take a list of numbers and sort them in ascending order.
# The core idea of bubble sort is to iterate through the list and swap adjacent elements if they are in the wrong order.
#
# Imagine we have a list of numbers:
# {{numbers = [5, 3, 8, 4, 2]}}
# {{numbers}}
#
# Too bad they're out of order! What does bubble sort do?
# Imagine we start at positions 0 and 1.
# The first two numbers are numbers[0] and numbers[1]. Let's see what happens after one iteration of bubble sort.
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=1)}}
#
# {{newNumbers}}
#
# We can see that the first two numbers are swapped.
# 
# Now let's try the second step.
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=2)}}
#
# {{newNumbers}}
#
# We are now comparing 5 and 8. These are in the correct order, so we move on to the next pair.
#
# {{newNumbers = include("/itomsmasher/bubbleSort", numbers, steps=3)}}
#
# {{include("/itomsmasher/arrayRender", newNumbers)}}
#
# We are now comparing 8 and 4. These are in the wrong order, so we swap them.
#
# We can render the full bubble sort process by setting steps to the length of the list.
# {{include("/itomsmasher/bubbleSortAnimate", numbers)}}
#
# {{return None}}



# DSL #2: VegaLite plus variables, and object inclusions

