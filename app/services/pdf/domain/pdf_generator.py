from typing import Protocol

class PdfGenerator(Protocol):
    """Protocol for PDF generation engines."""
    
    def generate(self, html_content: str) -> bytes:
        """
        Generates a PDF from HTML content.
        
        Args:
            html_content: The HTML string to convert to PDF.
            
        Returns:
            bytes: The generated PDF data.
        """
        ...
