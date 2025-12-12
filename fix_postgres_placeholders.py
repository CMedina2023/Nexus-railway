"""
Script para convertir todos los repositorios de SQLite a PostgreSQL
Reemplaza placeholders ? por %s y actualiza imports
"""
import os
import re

def fix_repository_file(filepath):
    """Corrige un archivo de repositorio para soportar PostgreSQL"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Actualizar imports
    content = content.replace('import sqlite3\n', '')
    
    # Actualizar import de get_db_connection
    if 'from app.database.db import get_db_connection\n' in content:
        content = content.replace(
            'from app.database.db import get_db_connection\n',
            'from app.database.db import get_db_connection, get_db\n'
        )
    elif 'from app.database.db import get_db_connection' in content and 'get_db' not in content:
        content = content.replace(
            'from app.database.db import get_db_connection',
            'from app.database.db import get_db_connection, get_db'
        )
    
    # 2. Reemplazar sqlite3.Error por Exception
    content = content.replace('sqlite3.Error', 'Exception')
    
    # 3. Encontrar y reemplazar todas las llamadas a cursor.execute con placeholders ?
    # Patrón para encontrar cursor.execute con ?
    pattern = r"(cursor\.execute\()(f?'''|f?\"\"\"|f?'|f?\")([^'\"]+?)(\2,?\s*\()"
    
    def replace_execute(match):
        prefix = match.group(1)  # cursor.execute(
        quote = match.group(2)   # ''' o """ o ' o "
        query = match.group(3)   # La consulta SQL
        suffix = match.group(4)  # ''', ( o similar
        
        # Si la consulta no tiene ?, no hacer nada
        if '?' not in query:
            return match.group(0)
        
        # Verificar si ya tiene la lógica de placeholder
        if 'placeholder' in query or '{placeholder}' in query:
            return match.group(0)
        
        # Contar placeholders
        placeholder_count = query.count('?')
        
        # Agregar lógica de detección de base de datos antes del execute
        # Buscar la indentación
        lines_before = content[:match.start()].split('\n')
        last_line = lines_before[-1] if lines_before else ''
        indent = len(last_line) - len(last_line.lstrip())
        base_indent = ' ' * indent
        
        # Crear el código de detección
        detection_code = f"{base_indent}db = get_db()\n{base_indent}placeholder = '%s' if db.is_postgres else '?'\n{base_indent}"
        
        # Reemplazar ? por {placeholder} en la consulta
        # Usar un contador para reemplazar uno por uno
        new_query = query
        for i in range(placeholder_count):
            new_query = new_query.replace('?', '{placeholder}', 1)
        
        # Cambiar a f-string si no lo es
        if not quote.startswith('f'):
            quote = 'f' + quote
        
        return detection_code + prefix + quote + new_query + suffix
    
    # Aplicar el reemplazo
    content = re.sub(pattern, replace_execute, content, flags=re.DOTALL)
    
    # Guardar solo si hubo cambios
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Actualizado: {os.path.basename(filepath)}")
        return True
    else:
        print(f"- Sin cambios: {os.path.basename(filepath)}")
        return False

def main():
    """Procesa todos los archivos de repositorio"""
    repo_dir = r'd:\Proyectos_python\Proyectos_AI\Nexus-railway\app\database\repositories'
    
    if not os.path.exists(repo_dir):
        print(f"Error: No se encuentra el directorio {repo_dir}")
        return
    
    files_updated = 0
    files_processed = 0
    
    for filename in os.listdir(repo_dir):
        if filename.endswith('_repository.py'):
            filepath = os.path.join(repo_dir, filename)
            files_processed += 1
            if fix_repository_file(filepath):
                files_updated += 1
    
    print(f"\n{'='*50}")
    print(f"Archivos procesados: {files_processed}")
    print(f"Archivos actualizados: {files_updated}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
