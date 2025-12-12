"""
Script de verificación para asegurar que todos los repositorios
están correctamente configurados para PostgreSQL
"""
import os
import re

def check_repository_file(filepath):
    """Verifica que un archivo de repositorio esté correctamente configurado"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    issues = []
    
    # 1. Verificar que no tenga import sqlite3
    if 'import sqlite3' in content:
        issues.append("❌ Todavía importa sqlite3")
    
    # 2. Verificar que no tenga sqlite3.Error
    if 'sqlite3.Error' in content:
        issues.append("❌ Todavía usa sqlite3.Error")
    
    # 3. Verificar si usa get_db_connection() (necesita placeholders dinámicos)
    uses_get_db_connection = 'get_db_connection()' in content
    
    # 4. Verificar si usa get_cursor() (ya tiene CursorWrapper)
    uses_get_cursor = 'get_cursor()' in content or 'self.db.get_cursor()' in content
    
    # 5. Si usa get_db_connection, verificar que tenga lógica de placeholder
    if uses_get_db_connection and not uses_get_cursor:
        if "placeholder = '%s' if" not in content and "{placeholder}" not in content:
            # Verificar si tiene queries con ?
            if re.search(r"VALUES\s*\([?]+", content) or re.search(r"WHERE.*\?", content):
                issues.append("❌ Usa get_db_connection() con placeholders ? sin conversión dinámica")
        else:
            issues.append("✅ Usa get_db_connection() con placeholders dinámicos")
    
    # 6. Si usa get_cursor, está OK (tiene CursorWrapper)
    if uses_get_cursor:
        issues.append("✅ Usa get_cursor() con CursorWrapper automático")
    
    return issues

def main():
    """Verifica todos los archivos de repositorio"""
    repo_dir = r'd:\Proyectos_python\Proyectos_AI\Nexus-railway\app\database\repositories'
    
    if not os.path.exists(repo_dir):
        print(f"Error: No se encuentra el directorio {repo_dir}")
        return
    
    print("="*70)
    print("VERIFICACIÓN DE REPOSITORIOS PARA POSTGRESQL")
    print("="*70)
    print()
    
    all_ok = True
    
    for filename in sorted(os.listdir(repo_dir)):
        if filename.endswith('_repository.py'):
            filepath = os.path.join(repo_dir, filename)
            issues = check_repository_file(filepath)
            
            print(f"📄 {filename}")
            if issues:
                for issue in issues:
                    print(f"   {issue}")
            else:
                print("   ✅ OK - Sin problemas detectados")
            
            # Verificar si hay errores
            has_errors = any('❌' in issue for issue in issues)
            if has_errors:
                all_ok = False
            
            print()
    
    print("="*70)
    if all_ok:
        print("✅ TODOS LOS REPOSITORIOS ESTÁN CORRECTAMENTE CONFIGURADOS")
    else:
        print("⚠️  ALGUNOS REPOSITORIOS NECESITAN CORRECCIÓN")
    print("="*70)

if __name__ == '__main__':
    main()
