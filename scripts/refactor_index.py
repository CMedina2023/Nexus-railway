
import re
import os

BASE_DIR = r"d:\Proyectos_python\Proyectos_AI\Nexus-railway"
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index.html")
CSS_PATH = os.path.join(BASE_DIR, "static", "css", "styles.css")
JS_PATH = os.path.join(BASE_DIR, "static", "js", "main.js")
NEW_TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index_refactored.html")

def refactor():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract CSS
    # Looking for <style>...</style>
    # We assume there is one main style block based on the view
    css_pattern = re.compile(r'<style>(.*?)</style>', re.DOTALL)
    css_match = css_pattern.search(content)
    
    css_content = ""
    if css_match:
        css_content = css_match.group(1).strip()
        # Remove the style block from content, replace with link
        content = content.replace(css_match.group(0), 
                                '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/styles.css\') }}">')
        
    # Extract JS
    # Looking for <script>...</script> that does not have src
    # There are multiple blocks. We should extract them all and append to main.js?
    # Or keep them separate?
    # Given the monolith nature, putting them in main.js is a good first step.
    
    js_content = []
    
    def replace_script(match):
        script_body = match.group(1)
        if "src=" in match.group(0): # This regex might be too simple if <script src=...> content </script> (unlikely)
            return match.group(0)
        
        # Check if it is a src script tag
        # The regex captured the content. We need to check the full tag.
        # Let's adjust regex.
        return match.group(0)

    # Better approach: Find all <script[^>]*>(.*?)</script>
    script_pattern = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL)
    
    matches = list(script_pattern.finditer(content))
    
    # We want to filter out scripts with src attribute
    inline_scripts = []
    replacement_map = {}
    
    for m in matches:
        attrs = m.group(1)
        body = m.group(2)
        full_match = m.group(0)
        
        if 'src=' not in attrs:
            inline_scripts.append(body.strip())
            # Mark for removal/replacement
            # We will replace the LAST inline script with the include, and remove others?
            # Or just replace each with nothing, and put the script tag at the end of body.
            replacement_map[full_match] = ""
            
    if inline_scripts:
        # Join all JS
        full_js = "\n\n// REFACTORED SECTION \n\n".join(inline_scripts)
        
        # Write JS
        with open(JS_PATH, 'w', encoding='utf-8') as f:
            f.write(full_js)
            
        # Write CSS
        with open(CSS_PATH, 'w', encoding='utf-8') as f:
            f.write(css_content)
            
        # Update HTML
        # Remove all inline scripts
        for original, replacement in replacement_map.items():
            content = content.replace(original, replacement)
            
        # Add the script tag at the end of body
        # Find </body>
        if '</body>' in content:
            content = content.replace('</body>', 
                                    '<script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>\n</body>')
        else:
            content += '\n<script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>'

    with open(NEW_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Extracted {len(css_content)} chars of CSS and {len(full_js)} chars of JS.")

if __name__ == "__main__":
    refactor()
