import csv
import io
from typing import List

from app.backend.story_parser import parse_story_data

def generate_jira_csv(stories: List[str]) -> str:
    """
    Genera un archivo CSV con los campos necesarios para importar a Jira.
    
    Args:
        stories: Lista de historias de usuario
        
    Returns:
        str: Contenido CSV como string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(['Summary', 'Description', 'Issuetype', 'Priority'])
    
    # Procesar cada historia
    for story in stories:
        data = parse_story_data(story)
        
        # Limpiar y escapar el contenido para CSV
        summary = data['summary'][:255] if data['summary'] else 'Sin título'
        description = data['description'].replace('"', '""')  # Escapar comillas
        issuetype = 'Story'
        priority = data['priority']
        
        writer.writerow([summary, description, issuetype, priority])
    
    return output.getvalue()
