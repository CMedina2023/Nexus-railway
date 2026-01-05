import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AdfConverter:
    """
    Utility class for converting text to Jira's Atlassian Document Format (ADF).
    """

    @staticmethod
    def convert(description: str) -> Dict[str, Any]:
        """
        Convierte una descripción con formato markdown simple a formato ADF de Jira.
        """
        if not description:
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }
        
        lines = description.split('\n')
        adf_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                adf_content.append({
                    "type": "paragraph",
                    "content": []
                })
                continue
            
            if line.startswith('* '):
                AdfConverter._process_bullet_point(line, adf_content)
            elif line.startswith('  • ') or line.startswith('• '):
                AdfConverter._process_sub_bullet(line, adf_content)
            else:
                adf_content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line, "marks": []}]
                })
        
        return {
            "type": "doc",
            "version": 1,
            "content": adf_content
        }

    @staticmethod
    def _process_bullet_point(line: str, adf_content: List[Dict]):
        text = line[2:].strip()
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                label = parts[0].strip()
                value = parts[1].strip()
                adf_content.append({
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "* ", "marks": []},
                        {"type": "text", "text": f"{label}:", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": f" {value}", "marks": []}
                    ]
                })
            else:
                adf_content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": f"* {text}", "marks": []}]
                })
        else:
            adf_content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": f"* {text}", "marks": []}]
            })

    @staticmethod
    def _process_sub_bullet(line: str, adf_content: List[Dict]):
        text = line.replace('•', '').strip()
        adf_content.append({
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "  • ", "marks": []},
                {"type": "text", "text": text, "marks": []}
            ]
        })
