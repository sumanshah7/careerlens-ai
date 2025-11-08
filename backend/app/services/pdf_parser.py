"""
PDF parser service for extracting text from PDF files
"""
import io
from typing import Optional
from pypdf import PdfReader


class PDFParser:
    """Parse PDF files and extract text"""
    
    def parse_pdf(self, pdf_bytes: bytes) -> str:
        """
        Parse PDF file and extract text
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            Extracted text from PDF
        """
        try:
            # Create PDF reader from bytes
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")


# Global instance
pdf_parser = PDFParser()

