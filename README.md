# ITOMS Project

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
python src/executor.py -add tests/bubbleSort.itom
```

### Running a program

To run a program by name:

```bash
python src/executor.py -run bubbleSort
```

This will generate an `output.png` file with the visual output.

## Test Files

- `tests/bubbleSort.itom` - Example bubble sort implementation