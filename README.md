# ITOMS Project

## Setup

Install dependencies and browsers:

```bash
pip install -r requirements.txt
playwright install
```

## Usage

To run the DSL processor on a test file:

```bash
python src/dslProcessor.py tests/bubbleSort.itom
```

This will yield a local file called `bubbleSort-output.png`

## Test Files

- `tests/bubbleSort.itom` - Example bubble sort implementation