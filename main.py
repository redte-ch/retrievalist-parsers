from pathlib import Path

from retrievalist_parsers.hierarchy.parser import HierarchyParser
from retrievalist_parsers.printer import JsonFilePrinter
from retrievalist_parsers.source import FileSource

# Using raw string (r) or forward slashes
path = r"D:\Prisha\SEM5\Extract-Heirarchy-from-Pdf\gettier 1 (2).pdf"
parser = HierarchyParser()

source = FileSource(path)

document = parser.parse_pdf(source)

printer = JsonFilePrinter()
file_path = Path("result.json")

printer.print(document, file_path=str(file_path.absolute()))
