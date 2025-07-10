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

## Test Files

- `tests/bubbleSort.itom` - Example bubble sort implementation

## Program Storage

Programs are stored in the `.programs` directory as individual folders containing:
- `program.json` - Program metadata and version history
- `code.itom` - Latest program source code
