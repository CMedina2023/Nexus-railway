
import re

FILE = r"d:\Proyectos_python\Proyectos_AI\Nexus-railway\templates\index_refactored.html"

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'class="modal-overlay"' in line:
        print(f"Modal at line {i+1}")
