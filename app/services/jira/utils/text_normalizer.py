import unicodedata
import re

def normalize(text: str) -> str:
    """
    Normaliza un texto eliminando acentos, caracteres especiales y convirtiendo a minúsculas.
    
    Args:
        text (str): El texto a normalizar.
        
    Returns:
        str: El texto normalizado.
    """
    if not text:
        return ""
    return re.sub(
        r'[^a-z0-9\s]', 
        '', 
        unicodedata.normalize('NFD', text.lower()).encode('ascii', 'ignore').decode()
    ).strip()
