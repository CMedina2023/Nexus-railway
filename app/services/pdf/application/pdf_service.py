import os
import logging
from typing import Optional
from app.services.pdf.domain.pdf_generator import PdfGenerator
from app.services.pdf.infrastructure.playwright_generator import PlaywrightPdfGenerator
from app.services.pdf.infrastructure.weasyprint_generator import WeasyPrintPdfGenerator

# Checking availability
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)

class PdfService:
    """
    Application service for PDF generation.
    Orchestrates the selection of the appropriate engine based on environment.
    """
    
    def __init__(self, playwright_gen: PdfGenerator, 
                 weasyprint_gen: PdfGenerator):
        """
        Initializes the service (DIP).
        """
        self.playwright_gen = playwright_gen
        self.weasyprint_gen = weasyprint_gen
        
    def _is_railway_environment(self) -> bool:
        """Detects if running on Railway."""
        return os.getenv('RAILWAY_ENVIRONMENT') is not None or os.getenv('RAILWAY_PROJECT_ID') is not None

    def get_engine_name(self) -> str:
        """
        Determines which PDF engine to use based on environment and availability.
        
        Returns:
            str: 'playwright' or 'weasyprint'
        """
        if self._is_railway_environment():
            if WEASYPRINT_AVAILABLE:
                logger.debug("Using WeasyPrint (Railway environment)")
                return 'weasyprint'
            else:
                logger.error("WeasyPrint not available in Railway")
                raise RuntimeError("WeasyPrint is not installed in Railway")
        
        # Local development
        if PLAYWRIGHT_AVAILABLE:
            logger.debug("Using Playwright (Local environment)")
            return 'playwright'
        elif WEASYPRINT_AVAILABLE:
            logger.warning("Playwright not available locally, using WeasyPrint as fallback")
            return 'weasyprint'
        else:
            logger.error("No PDF engine available (neither Playwright nor WeasyPrint)")
            raise RuntimeError("No PDF engine available. Install playwright or weasyprint.")

    def generate_pdf(self, html_content: str) -> bytes:
        """
        Entry point to generate a PDF.
        
        Args:
            html_content: The HTML content to convert.
            
        Returns:
            bytes: The generated PDF.
        """
        engine = self.get_engine_name()
        
        if engine == 'playwright':
            return self.playwright_gen.generate(html_content)
        else:
            return self.weasyprint_gen.generate(html_content)
