"""
Servicio para generación de archivos de salida
Responsabilidad única: Generar archivos CSV, JSON y ZIP
"""
import json
import zipfile
import logging
from typing import List, Dict
from io import StringIO

logger = logging.getLogger(__name__)


class FileGenerator:
    """Genera archivos de salida en diferentes formatos"""
    
    # Orden de columnas esperado para CSV de casos de prueba
    EXPECTED_CSV_COLUMNS = [
        "id_caso_prueba", "titulo_caso_prueba", "Descripcion", "Precondiciones",
        "Tipo_de_prueba", "Nivel_de_prueba", "Tipo_de_ejecucion", "Pasos",
        "Resultado_esperado", "Categoria", "Ambiente", "Ciclo", "issuetype",
        "Prioridad", "historia_de_usuario"
    ]
    
    def generate_csv(self, data: List[Dict], fieldnames: List[str] = None) -> str:
        """
        Genera CSV correctamente formateado para casos de prueba
        
        Args:
            data: Lista de diccionarios con los datos
            fieldnames: Lista opcional de nombres de columnas. 
                       Si no se proporciona, usa el orden esperado
            
        Returns:
            str: Contenido del CSV como string
        """
        import csv
        from io import StringIO
        
        if not data:
            return "id_caso_prueba,titulo_caso_prueba,Descripcion,Precondiciones\nTC001,No hay datos,No se generaron casos de prueba,\"\""
        
        # Determinar fieldnames
        if fieldnames is None:
            fieldnames = self._determine_fieldnames(data)
        
        # Generar CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Escribir datos
        for row in data:
            if isinstance(row, dict):
                # Asegurar que todas las claves estén presentes
                complete_row = {key: row.get(key, "") for key in fieldnames}
                writer.writerow(complete_row)
        
        csv_content = output.getvalue()
        logger.debug(f"CSV generado con {len(data)} filas y {len(fieldnames)} columnas")
        
        return csv_content
    
    def _determine_fieldnames(self, data: List[Dict]) -> List[str]:
        """Determina el orden de columnas basándose en los datos"""
        # Encontrar todas las claves presentes en los datos
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        # Ordenar las claves: primero las esperadas, luego las adicionales
        fieldnames = []
        for col in self.EXPECTED_CSV_COLUMNS:
            if col in all_keys:
                fieldnames.append(col)
                all_keys.remove(col)
        
        # Añadir las claves adicionales ordenadas
        fieldnames.extend(sorted(all_keys))
        
        return fieldnames
    
    def generate_json(self, data: any, indent: int = 2, ensure_ascii: bool = False) -> str:
        """
        Genera JSON formateado
        
        Args:
            data: Datos a serializar
            indent: Número de espacios para indentación
            ensure_ascii: Si debe escapar caracteres no ASCII
            
        Returns:
            str: Contenido del JSON como string
        """
        json_content = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        logger.debug(f"JSON generado con {len(json_content)} caracteres")
        return json_content
    
    def create_zip_file(
        self, 
        filepath: str, 
        files_to_add: Dict[str, str]
    ) -> None:
        """
        Crea un archivo ZIP con los archivos especificados
        
        Args:
            filepath: Ruta donde se guardará el ZIP
            files_to_add: Diccionario con nombre_archivo: contenido
        """
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files_to_add.items():
                if isinstance(content, str):
                    content = content.encode('utf-8')
                zip_file.writestr(filename, content)
        
        logger.info(f"ZIP creado: {filepath} con {len(files_to_add)} archivos")

