
import re
import os

BASE_DIR = r"d:\Proyectos_python\Proyectos_AI\Nexus-railway"
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index_refactored.html")
PARTIALS_DIR = os.path.join(BASE_DIR, "templates", "partials")

if not os.path.exists(PARTIALS_DIR):
    os.makedirs(PARTIALS_DIR)

def extract_block(content, start_marker, end_marker, output_filename):
    start = content.find(start_marker)
    if start == -1:
        print(f"Start marker not found for {output_filename}")
        return content, False

    # For end marker, we need to be careful about nesting.
    # But assuming these are top level blocks (sidebar, sections).
    # We can search for the end marker after start.
    
    # If using </section>, we might hit a nested one.
    # So we count tags?
    if end_marker == "</section>":
        # Simple tag counting
        cnt = 0
        pos = start
        while True:
            next_open = content.find("<section", pos + 1)
            next_close = content.find("</section>", pos + 1)
            
            if next_close == -1:
                print(f"End tag not found for {output_filename}")
                return content, False
                
            if next_open != -1 and next_open < next_close:
                cnt += 1
                pos = next_open
            else:
                if cnt == 0:
                    end = next_close + len(end_marker)
                    break
                cnt -= 1
                pos = next_close
    elif end_marker == "</aside>":
         end = content.find(end_marker, start) + len(end_marker)
    elif "modal" in output_filename:
         # Modals are usually divs. "modal-overlay"
         # Count divs
        cnt = 0
        pos = start
        while True:
            next_open = content.find("<div", pos + 1)
            next_close = content.find("</div>", pos + 1)
            
            if next_close == -1:
                 return content, False
            if next_open != -1 and next_open < next_close:
                cnt += 1
                pos = next_open
            else:
                if cnt == 0:
                    end = next_close + len("</div>")
                    break
                cnt -= 1
                pos = next_close
    else:
        end = content.find(end_marker, start) + len(end_marker)

    block = content[start:end]
    
    # Check if duplicate admin
    if output_filename == "admin.html":
        # Just save it. If we find another one, we handle it?
        pass

    with open(os.path.join(PARTIALS_DIR, output_filename), 'w', encoding='utf-8') as f:
        f.write(block)
        
    return content.replace(block, f"{{% include 'partials/{output_filename}' %}}"), True

def run():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Sidebar
    content, _ = extract_block(content, '<aside class="sidebar"', '</aside>', 'sidebar.html')

    # 2. Sections
    sections = [
        ('dashboard', 'dashboard.html'),
        ('infografia', 'infografia.html'),
        ('metricas', 'metricas.html'),
        ('jira-carga-masiva', 'jira_carga_masiva.html'),
        ('jira-reportes', 'jira_reportes.html'),
        ('crear-historias', 'crear_historias.html'),
        ('crear-casos-prueba', 'crear_casos_prueba.html'),
        ('feedback', 'feedback.html'),
        ('admin', 'admin.html')
    ]

    for sid, filename in sections:
        # We need to loop because admin might appear twice
        while True:
            start_tag = f'<section id="{sid}"'
            if start_tag not in content:
                break
            
            # Special handling for admin to wrap if block?
            # The current extractor extracts just the section tag.
            # But admin is wrapped in {% if ... %}. 
            # We should try to extract the surrounding if?
            # Let's just extract the section for now. The if will remain in index.html or we move it?
            # Ideally move the if inside the partial? Or keep logic in index?
            # Keeping logic in index is safer for now.
            
            new_content, success = extract_block(content, start_tag, '</section>', filename)
            if success:
                content = new_content
                print(f"Extracted {filename}")
            else:
                break

    # 3. Modal
    content, _ = extract_block(content, '<div class="modal-overlay"', '</div>', 'guide_modal.html')

    # 4. Final Cleanup
    # If there are duplicate includes (like admin), we might want to remove one?
    # Or leave them.
    
    with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    run()
