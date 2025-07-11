from dslProcessor import DSLProcessor
from programs import ProgramOutput, ProgramDirectory
from typing import List, Dict
import time
import re
from playwright.sync_api import sync_playwright


class SpreadsheetDSLProcessor(DSLProcessor):
    def __init__(self, programDirectory: ProgramDirectory):
        super().__init__()
        self.programDirectory = programDirectory
    
    def getVisualReturnTypes(self) -> List[str]:
        return ["html", "png"]
    
    def process(self, code: str, input: dict, outputNames: List[str], preferredVisualReturnType: str) -> ProgramOutput:
        if preferredVisualReturnType not in self.getVisualReturnTypes():
            raise ValueError(f"Invalid visual return type: {preferredVisualReturnType}")
        
        # Parse spreadsheet definition
        grid = self._parseSpreadsheet(code, input)

        # Calculate all formulas
        calculated_grid = self._calculateFormulas(grid)
        # Generate visual output
        if preferredVisualReturnType == "html":
            visualOutput = self._generateHtmlTable(calculated_grid)
        else:  # png
            visualOutput = self._generatePngTable(calculated_grid)

        # Extract output data
        outputData = {}
        for outputName in outputNames:
            if outputName in calculated_grid:
                outputData[outputName] = calculated_grid[outputName]
        
        return ProgramOutput(time.time(), preferredVisualReturnType, visualOutput, outputData)
    
    def _parseSpreadsheet(self, code: str, input: dict) -> Dict:
        """Parse spreadsheet definition from code"""
        grid = {}
        
        # Parse cell definitions like A1: 10, B2: =SUM(A1:A5)
        cell_pattern = r'([A-Z]+\d+):\s*(.+)'
        
        for line in code.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            match = re.match(cell_pattern, line)
            if match:
                cell_ref = match.group(1)
                value = match.group(2).strip()
                # If value is surrounded by double braces, replace with the parameter value of the variable
                if value.startswith('{{') and value.endswith('}}'):
                    value = value[2:-2]
                    value = input[value]
                else:
                    # If value is not surrounded by double braces, it's a literal value
                    value = value.strip()

                grid[cell_ref] = value
        
        return grid
    
    def _calculateFormulas(self, grid: Dict) -> Dict:
        """Calculate all formulas in the grid"""
        calculated = {}
        
        # First pass: handle non-formula values
        for cell_ref, value in grid.items():
            if not value.startswith('='):
                try:
                    calculated[cell_ref] = float(value)
                except ValueError:
                    calculated[cell_ref] = value
        
        # Second pass: handle formulas (simple implementation)
        for cell_ref, value in grid.items():
            if value.startswith('='):
                formula = value[1:]  # Remove =
                calculated[cell_ref] = self._evaluateFormula(formula, calculated)
        
        return calculated
    
    def _evaluateFormula(self, formula: str, calculated: Dict) -> float:
        """Evaluate a formula"""
        # Simple formula evaluation for basic functions
        
        # SUM function
        if formula.startswith('SUM('):
            range_match = re.match(r'SUM\(([A-Z]+\d+):([A-Z]+\d+)\)', formula)
            if range_match:
                start_cell = range_match.group(1)
                end_cell = range_match.group(2)
                return self._sumRange(start_cell, end_cell, calculated)
        
        # AVERAGE function
        elif formula.startswith('AVERAGE('):
            range_match = re.match(r'AVERAGE\(([A-Z]+\d+):([A-Z]+\d+)\)', formula)
            if range_match:
                start_cell = range_match.group(1)
                end_cell = range_match.group(2)
                return self._averageRange(start_cell, end_cell, calculated)
        
        # MAX function
        elif formula.startswith('MAX('):
            range_match = re.match(r'MAX\(([A-Z]+\d+):([A-Z]+\d+)\)', formula)
            if range_match:
                start_cell = range_match.group(1)
                end_cell = range_match.group(2)
                return self._maxRange(start_cell, end_cell, calculated)
        
        # MIN function
        elif formula.startswith('MIN('):
            range_match = re.match(r'MIN\(([A-Z]+\d+):([A-Z]+\d+)\)', formula)
            if range_match:
                start_cell = range_match.group(1)
                end_cell = range_match.group(2)
                return self._minRange(start_cell, end_cell, calculated)
        
        # Simple arithmetic with cell references
        else:
            # Replace cell references with values
            for cell_ref, value in calculated.items():
                if isinstance(value, (int, float)):
                    formula = formula.replace(cell_ref, str(value))
            
            try:
                return eval(formula)  # Simple evaluation
            except:
                return 0.0
        
        return 0.0
    
    def _sumRange(self, start_cell: str, end_cell: str, calculated: Dict) -> float:
        """Sum values in a range"""
        cells = self._getCellsInRange(start_cell, end_cell)
        total = 0.0
        for cell in cells:
            if cell in calculated and isinstance(calculated[cell], (int, float)):
                total += calculated[cell]
        return total
    
    def _averageRange(self, start_cell: str, end_cell: str, calculated: Dict) -> float:
        """Average values in a range"""
        cells = self._getCellsInRange(start_cell, end_cell)
        values = []
        for cell in cells:
            if cell in calculated and isinstance(calculated[cell], (int, float)):
                values.append(calculated[cell])
        return sum(values) / len(values) if values else 0.0
    
    def _maxRange(self, start_cell: str, end_cell: str, calculated: Dict) -> float:
        """Max value in a range"""
        cells = self._getCellsInRange(start_cell, end_cell)
        values = []
        for cell in cells:
            if cell in calculated and isinstance(calculated[cell], (int, float)):
                values.append(calculated[cell])
        return max(values) if values else 0.0
    
    def _minRange(self, start_cell: str, end_cell: str, calculated: Dict) -> float:
        """Min value in a range"""
        cells = self._getCellsInRange(start_cell, end_cell)
        values = []
        for cell in cells:
            if cell in calculated and isinstance(calculated[cell], (int, float)):
                values.append(calculated[cell])
        return min(values) if values else 0.0
    
    def _getCellsInRange(self, start_cell: str, end_cell: str) -> List[str]:
        """Get all cells in a range like A1:A5"""
        start_col = re.match(r'([A-Z]+)', start_cell).group(1)
        start_row = int(re.match(r'[A-Z]+(\d+)', start_cell).group(1))
        end_col = re.match(r'([A-Z]+)', end_cell).group(1)
        end_row = int(re.match(r'[A-Z]+(\d+)', end_cell).group(1))
        
        cells = []
        # Simple implementation for single column ranges
        if start_col == end_col:
            for row in range(start_row, end_row + 1):
                cells.append(f"{start_col}{row}")
        
        return cells
    
    def _generateHtmlTable(self, grid: Dict) -> str:
        """Generate HTML table from grid"""
        if not grid:
            return "<table><tr><td>Empty spreadsheet</td></tr></table>"
        
        # Find grid dimensions
        max_row = 0
        max_col = 0
        for cell_ref in grid.keys():
            col_match = re.match(r'([A-Z]+)', cell_ref)
            row_match = re.match(r'[A-Z]+(\d+)', cell_ref)
            if col_match and row_match:
                col = col_match.group(1)
                row = int(row_match.group(1))
                max_row = max(max_row, row)
                max_col = max(max_col, ord(col) - ord('A') + 1)
        
        html = "<table border='1' style='border-collapse: collapse;'>"
        
        # Header row
        html += "<tr><th></th>"
        for col_idx in range(max_col):
            col_letter = chr(ord('A') + col_idx)
            html += f"<th>{col_letter}</th>"
        html += "</tr>"
        
        # Data rows
        for row in range(1, max_row + 1):
            html += f"<tr><th>{row}</th>"
            for col_idx in range(max_col):
                col_letter = chr(ord('A') + col_idx)
                cell_ref = f"{col_letter}{row}"
                value = grid.get(cell_ref, "")
                html += f"<td>{value}</td>"
            html += "</tr>"
        
        html += "</table>"
        return html
    
    def _generatePngTable(self, grid: Dict) -> bytes:
        """Generate PNG image from grid (simple text-based)"""
        # For now, return HTML as PNG would require additional dependencies
        html = self._generateHtmlTable(grid)

        # Convert HTML to PNG
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            png_bytes = page.screenshot(full_page=True, type="png")
            browser.close()
            return png_bytes














