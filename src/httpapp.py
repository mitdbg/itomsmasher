# Implement a basic http app that can be used to serve the itom viewer

from flask import Flask, request, send_file
from programs import ProgramDirectory, ProgramInput
from programExecutor import ProgramExecutor
import io
import os
import time

app = Flask(__name__)

# Initialize program directory and executor
localProgramDir = ".programs" 
if not os.path.exists(localProgramDir):
    os.makedirs(localProgramDir)

programDirectory = ProgramDirectory(localProgramDir)
programExecutor = ProgramExecutor(programDirectory)

defaultProgramDict = dict([(p.name, {"name": p.name, "description": p.description, "inputDescription": ",".join(p.inputs)}) for p in programDirectory.getPrograms()])

@app.route('/')
def index():
    # List all available programs
    programs = programDirectory.getPrograms()
    # Add some CSS style to make the font bigger
    html = "<style>body { font-size: 1.2em; }</style>"
    html += "<h1>Available Programs</h1>"
    html += "<ul>"
    for program in programs:
        html += f'<li><a href="/view/{program.name}">{program.name}</a>: {program.description}</li>'
    html += "</ul>"
    return html

@app.route('/view/<program_name>')
def view_program(program_name):
    # Execute the itomViewer program with the requested program
    try:
        inputs = {"__programs__": defaultProgramDict,
                  "programName": program_name}
        programInput = ProgramInput(startTimestamp=int(time.time()), inputs=inputs)
        output = programExecutor.executeProgram(
            "itomViewer", 
            programInput,
            preferredVisualReturnType="html",
            inferInputs=True,
            callingProgramContext=program_name
        )
        html = output.viz()
        return html

    except Exception as e:
        print("Error: ", e)
        return f"Error viewing program: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

