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

css = """
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
"""        

@app.route('/')
def index():
    # List all available programs
    programs = programDirectory.getPrograms()
    # Add some CSS style to make the font bigger
    from jinja2 import Environment, BaseLoader, pass_context

    cssAppend = """
    tbody tr {
        cursor: pointer;
    }
    tbody tr:hover {
        background-color: rgb(210, 210, 210); /* optional: subtle hover highlight */
    }
"""
    templateCode = """
    <style>{{css}}</style>
    <style>{{cssAppend}}</style>
    <h1><a href="/" style="text-decoration: none; color: inherit;"><span>🧠</span></a> Available Programs</h1>
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
                <tr style="background-color: rgb(229,228,228); margin-bottom: 8px;" data-href="/view/{{program.name}}">
                    <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                        {{program.name}}
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
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            document.querySelectorAll("tbody tr").forEach(function(row) {
                row.addEventListener("click", function() {
                    const href = row.getAttribute("data-href");
                    if (href) {
                        window.location = href;
                    }
                });
            });
        });
    </script>
"""
    def datetimeformat(value, format="%Y-%m-%d %H:%M"):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime("%B %d, %Y %I:%M %p")

    env = Environment(loader=BaseLoader)
    env.filters["datetimeformat"] = datetimeformat
    template = env.from_string(templateCode)
    html = template.render(programs=programs, css=css, cssAppend=cssAppend)
    return html

@app.route('/rendered/<program_id>')
def rendered(program_id):
    return "Test result for program " + program_id

@app.route('/view/<program_name>')
def view_program(program_name):
    program = programDirectory.getProgram(program_name)

    templateCode = """
    <style>{{css}}</style>

    <h1><a href="/" style="text-decoration: none; color: inherit;"><span>🧠</span></a> Program Details</h1>
    <div style="background-color: rgb(229,228,228); border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h1>{{program.name}}</h1>
    <p>{{program.description}}</p>
    <p>Program Type: <span style="font-family: Courier, monospace; background-color: #e0e0e0; padding: 2px 6px; border-radius: 4px;">{{program.dslId}}</span></p>
    <p>Last Modified: {{program.modified | datetimeformat}}</p>
    </div>

    <div style="background-color: rgb(229,228,228); border-radius: 8px; padding: 20px; margin: 20px 0;">
    <h2>Test Inputs</h2>

    {% if not program.inputs %}
        <p>No inputs</p>
    {% else %}
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <thead>
            <tr style="background-color: rgb(210,210,210);">
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Parameter</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Description</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Required</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Default Value</th>
                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Value</th>
            </tr>
        </thead>
        <tbody>
            {% for param_name, param_info in program.inputs.items() %}
            <tr style="background-color: rgb(240,240,240);">
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{{param_name}}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{{param_info.get('description', '')}}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{{param_info.get('required', False)}}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">{{param_info.get('default', '')}}</td>
                <td style="padding: 12px; border-bottom: 1px solid #ddd;">
                    <input type="text" 
                           id="param_{{param_name}}"
                           name="{{param_name}}"
                           value="{{param_info.get('default', '')}}"
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    {% endif %}
    </div>

    <div style="margin: 20px 0;">
    <div style="display: inline-block; margin-right: 10px;">
        <button id="codeButton" style="padding: 8px 16px; border-radius: 4px; border: none; background-color: #007bff; color: white; cursor: pointer;">Code</button>
    </div>
    <div style="display: inline-block;">
        <button id="documentButton" style="padding: 8px 16px; border-radius: 4px; border: none; background-color: #e0e0e0; color: black; cursor: pointer;">Document</button>
    </div>
    </div>

    <div id="codeView" style="display: block;">
    <div style="background-color: rgb(229,228,228); border-radius: 8px; padding: 20px; margin: 20px 0; font-family: Courier, monospace;">
        <pre style="white-space: pre-wrap;">{{program.getLatestCode()}}</pre>
    </div>
    </div>

    <div id="documentView" style="display: none;">
    <div id="documentContent" style="background-color: white; padding: 20px; border-radius: 8px; min-height: 400px;">
        <!-- AJAX-loaded content will appear here -->
        <em>Loading...</em>
    </div>
    </div>

    <script>
    document.addEventListener("DOMContentLoaded", function() {
        const codeButton = document.getElementById("codeButton");
        const documentButton = document.getElementById("documentButton");
        const codeView = document.getElementById("codeView");
        const documentView = document.getElementById("documentView");
        const documentContent = document.getElementById("documentContent");

        let documentLoaded = false;

        codeButton.addEventListener("click", function() {
        codeButton.style.backgroundColor = "#007bff";
        codeButton.style.color = "white";
        documentButton.style.backgroundColor = "#e0e0e0";
        documentButton.style.color = "black";
        codeView.style.display = "block";
        documentView.style.display = "none";
        });

        documentButton.addEventListener("click", function() {
        documentButton.style.backgroundColor = "#007bff";
        documentButton.style.color = "white";
        codeButton.style.backgroundColor = "#e0e0e0";
        codeButton.style.color = "black";
        documentView.style.display = "block";
        codeView.style.display = "none";

        if (!documentLoaded) {
            fetch("/rendered/{{program.name}}")
            .then(response => {
                if (!response.ok) throw new Error("Failed to load document");
                return response.text();
            })
            .then(html => {
                documentContent.innerHTML = html;
                documentLoaded = true;
            })
            .catch(error => {
                documentContent.innerHTML = "<p style='color: red;'>Error loading document.</p>";
                console.error(error);
            });
        }
        });
    });
    </script>
    """

    def datetimeformat(value, format="%Y-%m-%d %H:%M"):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime("%B %d, %Y %I:%M %p")

    env = Environment(loader=BaseLoader)
    env.filters["datetimeformat"] = datetimeformat
    template = env.from_string(templateCode)
    html = template.render(program=program, css=css)
    return html


#    # Execute the itomViewer program with the requested program
#    try:
#        inputs = {"__programs__": defaultProgramDict,
#                  "programName": program_name}
#        programInput = ProgramInput(startTimestamp=int(time.time()), inputs=inputs)
#        output = programExecutor.executeProgram(
#            "itomViewer", 
#            programInput,
#            preferredVisualReturnType="html",#
#            inferInputs=True#,
#            callingProgramContext=program_name
#        )
#        html = output.viz()
#        return html
#
#    except Exception as e:
#        print("Error: ", e)
#        return f"Error viewing program: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

