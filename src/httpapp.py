#! /usr/bin/env python3
# Implement a basic http app that can be used to serve the itom viewer

from flask import Flask, request, send_file
from programs import ProgramDirectory, ProgramInput
from programExecutor import ProgramExecutor
from jinja2 import Environment, BaseLoader, pass_context
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
    css = """<style>
        body {
            background-color: rgb(246,190,23);
            margin: 0;
            font-size: 1.2em;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            padding: 1em;
        }
        h1, p {
            margin: 0.25em 0;
        }
</style>        
"""        
    from jinja2 import Environment, BaseLoader, pass_context

    templateCode = """
    {{css}}
    <h1>Available Programs</h1>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <thead>
            <tr style="background-color: rgb(229,228,228);">
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Program Name</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Program Type</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Created</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Last Modified</th>
            </tr>
        </thead>
        <tbody>
            {% for program in programs %}
                <tr style="background-color: rgb(229,228,228); margin-bottom: 8px;">
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        <a href="/view/{{program.name}}" style="display: block; text-decoration: none; color: inherit;" onclick="window.location='/view/{{program.name}}'; return false;">{{program.name}}</a>
                        <script>
                            document.currentScript.parentElement.parentElement.parentElement.onclick = function() {
                                window.location = '/view/{{program.name}}';
                            }
                        </script>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        {{program.description}}
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        {{program.dslId}}
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        {{program.created | datetimeformat}}
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        {{program.modified | datetimeformat}}
                    </td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
"""
    def datetimeformat(value, format="%Y-%m-%d %H:%M"):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime("%B %d, %Y %I:%M %p")

    env = Environment(loader=BaseLoader)
    env.filters["datetimeformat"] = datetimeformat
    template = env.from_string(templateCode)
    html = template.render(programs=programs, css=css)
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

