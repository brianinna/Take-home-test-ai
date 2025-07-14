"""
OCR engine module, provides image text recognition functionality.
"""
import io
import logging
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR engine, responsible for image text recognition.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR engine
        
        Args:
            tesseract_path: Installation path of Tesseract OCR engine (optional)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Process image, extract text
        
        Args:
            image_data: Binary data of the image
            
        Returns:
            Dictionary containing OCR results
        """
        try:
            # Read image
            image = Image.open(io.BytesIO(image_data))
            
            # Image preprocessing (improve OCR quality)
            image = self._preprocess_image(image)
            
            # OCR processing
            ocr_result = pytesseract.image_to_string(
                image,
                lang='eng',  # Change language as needed
                config='--psm 6'  # Assume block text
            )
            
            # Get more detailed OCR information (including confidence and position)
            ocr_data = pytesseract.image_to_data(
                image, 
                lang='eng',
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            avg_confidence = avg_confidence / 100  # Convert to 0-1 range
            
            return {
                "text": ocr_result,
                "confidence": avg_confidence,
                "word_count": len(ocr_result.split())
            }
            
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Image preprocessing, improve OCR quality
        
        Args:
            image: PIL Image object
            
        Returns:
            Processed image
        """
        # Convert to grayscale image
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        
        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)
        
        # Binarization (adjust threshold as needed)
        # threshold = 150
        # image = image.point(lambda p: 255 if p > threshold else 0)
        
        return image
