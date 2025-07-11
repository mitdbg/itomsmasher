# ITOMS Project

Interactive Text-based Object Management System - A DSL processor for executing programs with visual output.

## Setup

Install dependencies and browsers:

```bash
pip install -r requirements.txt
playwright install
```

## Usage

### Adding a program

To add a new program to the local program directory:

```bash
python src/executor.py -add <program_name> -source <source_file>
```

Example:
```bash
python src/executor.py -add bubbleSort -source tests/bubbleSort.itom
```

### Running a program

To run a program by name with specified output format and file:

```bash
python src/executor.py -run <program_name> -output <output_file> -format <format>
```

Example:
```bash
python src/executor.py -run bubbleSort -output bubbleSort.png -format png
```

Supported formats: `png`, `html`

Keep in mind you will have to add all included programs in order to execute a top-level program successfully

### Listing programs

To see all available programs:

```bash
python src/executor.py -status
```

## DSL Types and Examples

ITOMS supports three different DSL processors for different types of programs:

### 1. Basic DSL (Markdown with Variables)
**File**: `basicDslProcessor.py`
**Description**: Processes markdown documents with embedded variables and includes for creating interactive documentation.

**Example** (`tests/bubbleSort.itom`):
```
# Welcome to Bubble Sort

We have a list of numbers:
{{numbers = [5, 3, 8, 4, 2]}}

Current list: {{numbers}}

After sorting: {{include("bubbleSortAlgorithm", numbers)}}
```

**Usage**:
```bash
python src/executor.py -add bubbleSort -source tests/bubbleSort.itom
python src/executor.py -run bubbleSort -output bubbleSort.png -format png
```

### 2. AI Image DSL 
**File**: `aiImageDslProcessor.py`
**Description**: Generates images using OpenAI's DALL-E API based on text prompts with variable substitution.

**Example** (`tests/aiImagePrompt.itom`):
```
{{subject = "a futuristic city"}}
{{style = "cyberpunk"}}
{{size = "large"}}

A beautiful {{subject}} in {{style}} style with neon lights and flying cars
```

**Usage**:
```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY="your-api-key-here"
python src/executor.py -add aiImage -source tests/aiImagePrompt.itom
python src/executor.py -run aiImage -output aiImage.png -format png
```

### 3. Spreadsheet DSL
**File**: `spreadsheetDslProcessor.py`
**Description**: Creates interactive spreadsheets with cells, formulas, and basic functions.

**Example** (`tests/testSpreadsheet.itom`):
```
# Sample budget spreadsheet
A1: Income
A2: 5000
A3: 3000
A4: 2000

B1: Expenses
B2: 1500
B3: 800
B4: 600

C1: Total Income
C2: =SUM(A2:A4)
C3: Total Expenses
C4: =SUM(B2:B4)
C5: Net
C6: =C2-C4
```

**Usage**:
```bash
python src/executor.py -add spreadsheet -source tests/testSpreadsheet.itom
python src/executor.py -run spreadsheet -output spreadsheet.html -format html
```

**Supported Functions**:
- `SUM(range)` - Sum values in a range
- `AVERAGE(range)` - Average values in a range  
- `MAX(range)` - Maximum value in a range
- `MIN(range)` - Minimum value in a range
- Basic arithmetic with cell references

## Test Files

- `tests/bubbleSort.itom` - Interactive bubble sort documentation (Basic DSL)
- `tests/aiImagePrompt.itom` - AI image generation example (AI Image DSL)
- `tests/testSpreadsheet.itom` - Budget spreadsheet example (Spreadsheet DSL)

## Program Storage

Programs are stored in the `.programs` directory as individual folders containing:
- `program.json` - Program metadata and version history
- `code.itom` - Latest program source code
