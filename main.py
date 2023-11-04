from pdfstructure.printer import JsonFilePrinter
from pdfstructure.hierarchy.parser import HierarchyParser
from pdfstructure.source import FileSource
from pathlib import Path

path = r"D:\Prisha\SEM5\Extract-Heirarchy-from-Pdf\gettier 1 (2).pdf"  # Using raw string (r) or forward slashes
parser = HierarchyParser()

source = FileSource(path)

document = parser.parse_pdf(source)

printer = JsonFilePrinter()
file_path = Path("result.json")

printer.print(document, file_path=str(file_path.absolute()))
