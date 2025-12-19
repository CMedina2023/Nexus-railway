
import re

FILE = r"d:\Proyectos_python\Proyectos_AI\Nexus-railway\templates\index_refactored.html"
OUT = r"d:\Proyectos_python\Proyectos_AI\Nexus-railway\structure.txt"

def analyze():
    with open(FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(OUT, 'w', encoding='utf-8') as f_out:
        for i, line in enumerate(lines):
            if '<section' in line:
                # Extract id and class
                id_match = re.search(r'id="([^"]+)"', line)
                class_match = re.search(r'class="([^"]+)"', line)
                
                sid = id_match.group(1) if id_match else "no-id"
                sclass = class_match.group(1) if class_match else "no-class"
                
                f_out.write(f"Line {i+1}: <section id='{sid}' class='{sclass}'>\n")

if __name__ == "__main__":
    analyze()
