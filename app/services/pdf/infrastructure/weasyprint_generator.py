import logging
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)

class WeasyPrintPdfGenerator:
    """PDF generator implementation using WeasyPrint."""
    
    def generate(self, html_content: str) -> bytes:
        """
        Generates a PDF using WeasyPrint (optimized for Railway/serverless environments).
        
        Args:
            html_content: HTML content to convert.
            
        Returns:
            bytes: Generated PDF content.
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is not installed.")
            
        try:
            # Create HTML object from the rendered string
            html = HTML(string=html_content, base_url='.')
            
            # Define CSS styles for landscape (A4 horizontal)
            css = CSS(string='''
                @page {
                    size: A4 landscape;
                    margin: 10mm;
                }
            ''')
            
            # Generate PDF in memory
            pdf_buffer = html.write_pdf(stylesheets=[css])
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF with WeasyPrint: {e}", exc_info=True)
            raise
