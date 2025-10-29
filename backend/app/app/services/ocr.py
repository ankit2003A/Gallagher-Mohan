# backend/app/services/ocr.py
import os
import pytesseract
from PIL import Image, ImageFile
import logging
from typing import List
from pdf2image import convert_from_path
import tempfile

# Configure logging
logger = logging.getLogger(__name__)

# Allow PIL to load truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

def extract_text(file_path: str) -> str:
    """
    Extract text from an image or PDF file using Tesseract OCR.
    
    Args:
        file_path: Path to the image or PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.pdf':
            return _extract_text_from_pdf(file_path)
        else:
            return _extract_text_from_image(file_path)
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise

def _extract_text_from_image(image_path: str) -> str:
    """Extract text from an image file."""
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale for better OCR results
            img = img.convert('L')
            # Use Tesseract to extract text
            text = pytesseract.image_to_string(img)
            return text.strip()
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        raise

def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file by converting each page to an image."""
    try:
        # Use the correct Poppler path
        POPPLER_PATH = r"C:\poppler\poppler-25.07.0\Library\bin"
        
        # Create a temporary directory to store the converted images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to a list of images (one per page)
            images = convert_from_path(
                pdf_path,
                output_folder=temp_dir,
                fmt='jpeg',
                thread_count=4,
                poppler_path=POPPLER_PATH
            )
            
            # Extract text from each page
            full_text = []
            for i, image in enumerate(images):
                # Convert to grayscale for better OCR results
                image = image.convert('L')
                # Extract text from the page
                text = pytesseract.image_to_string(image)
                full_text.append(text.strip())
                
            return '\n\n'.join(full_text)
            
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        raise