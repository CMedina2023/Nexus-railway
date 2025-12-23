import logging
from playwright.sync_api import sync_playwright
from app.services.pdf.domain.pdf_generator import PdfGenerator

logger = logging.getLogger(__name__)

class PlaywrightPdfGenerator:
    """PDF generator implementation using Playwright."""
    
    def generate(self, html_content: str) -> bytes:
        """
        Generates a PDF using Playwright (optimized for local environments).
        
        Args:
            html_content: HTML content to convert.
            
        Returns:
            bytes: Generated PDF content.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Load the HTML
                page.set_content(html_content, wait_until='networkidle')
                
                # Generate PDF with landscape configuration
                pdf_buffer = page.pdf(
                    format='A4',
                    landscape=True,
                    margin={
                        'top': '10mm',
                        'right': '10mm',
                        'bottom': '10mm',
                        'left': '10mm'
                    },
                    print_background=True
                )
                
                browser.close()
                return pdf_buffer
                
        except Exception as e:
            logger.error(f"Error generating PDF with Playwright: {e}", exc_info=True)
            raise
