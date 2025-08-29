"""
OCR Processing Module for Document Intelligence
Handles image preprocessing, OCR extraction, and text analysis
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from pdf2image import convert_from_bytes
import io

class OCRProcessor:
    def __init__(self):
        """Initialize OCR processor with default configurations"""
        self.tesseract_config = '--oem 3 --psm 6'
        self.confidence_threshold = 30
        
    def preprocess_image(self, image: np.ndarray, 
                        grayscale: bool = True,
                        denoise: bool = True, 
                        deskew: bool = True,
                        upscale: bool = True,
                        binarize: bool = True) -> np.ndarray:
        """
        Apply preprocessing steps to improve OCR accuracy
        
        Args:
            image: Input image as numpy array
            grayscale: Convert to grayscale
            denoise: Apply noise reduction
            deskew: Correct image skew
            upscale: Increase image resolution
            binarize: Apply binary thresholding
            
        Returns:
            Preprocessed image
        """
        processed = image.copy()
        
        # Convert to grayscale
        if grayscale and len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
        
        # Upscale image for better OCR
        if upscale:
            height, width = processed.shape[:2]
            processed = cv2.resize(processed, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        if denoise:
            processed = cv2.medianBlur(processed, 3)
            processed = cv2.bilateralFilter(processed, 9, 75, 75)
        
        # Deskew
        if deskew:
            processed = self._deskew_image(processed)
        
        # Binarize
        if binarize:
            processed = cv2.adaptiveThreshold(
                processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
        
        return processed
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct image skew"""
        try:
            # Calculate skew angle
            coords = np.column_stack(np.where(image > 0))
            if len(coords) < 10:
                return image
                
            angle = cv2.minAreaRect(coords)[-1]
            
            # Normalize angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Only correct significant skew (> 0.5 degrees)
            if abs(angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), 
                                       flags=cv2.INTER_CUBIC, 
                                       borderMode=cv2.BORDER_REPLICATE)
                return rotated
        except:
            pass
        
        return image
    
    def extract_text_with_boxes(self, image: np.ndarray) -> Dict:
        """
        Extract text with bounding box information and confidence scores
        
        Args:
            image: Preprocessed image
            
        Returns:
            Dictionary containing text, boxes, and confidence scores
        """
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
            
            words = []
            boxes = []
            confidences = []
            
            for i in range(len(data['text'])):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence > self.confidence_threshold and text:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    words.append(text)
                    boxes.append((x, y, x + w, y + h))
                    confidences.append(confidence)
            
            # Also get clean text
            clean_text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            return {
                'text': clean_text,
                'words': words,
                'boxes': boxes,
                'confidences': confidences,
                'word_count': len(words),
                'avg_confidence': np.mean(confidences) if confidences else 0
            }
            
        except Exception as e:
            logging.error(f"OCR extraction failed: {e}")
            return {
                'text': '',
                'words': [],
                'boxes': [],
                'confidences': [],
                'word_count': 0,
                'avg_confidence': 0
            }
    
    def process_pdf(self, pdf_bytes: bytes, page_num: int = 0) -> np.ndarray:
        """
        Convert PDF page to image for OCR processing
        
        Args:
            pdf_bytes: PDF file as bytes
            page_num: Page number to process (0-indexed)
            
        Returns:
            Image as numpy array
        """
        try:
            # Convert PDF to images
            images = convert_from_bytes(pdf_bytes, dpi=300, first_page=page_num+1, last_page=page_num+1)
            
            if images:
                # Convert PIL to numpy array
                img_array = np.array(images[0])
                return img_array
            else:
                raise ValueError("Could not convert PDF page to image")
                
        except Exception as e:
            logging.error(f"PDF processing failed: {e}")
            raise
    
    def process_document(self, file_bytes: bytes, file_type: str, 
                        preprocessing_options: Optional[Dict] = None) -> Dict:
        """
        Main processing function for documents
        
        Args:
            file_bytes: Document file as bytes
            file_type: File extension (pdf, jpg, png, etc.)
            preprocessing_options: Preprocessing configuration
            
        Returns:
            OCR results with extracted text and metadata
        """
        if preprocessing_options is None:
            preprocessing_options = {
                'grayscale': True,
                'denoise': True,
                'deskew': True,
                'upscale': True,
                'binarize': True
            }
        
        try:
            # Load image based on file type
            if file_type.lower() == 'pdf':
                image = self.process_pdf(file_bytes)
            else:
                # Handle image files
                image = np.array(Image.open(io.BytesIO(file_bytes)))
            
            # Store original for display
            original_image = image.copy()
            
            # Preprocess image
            processed_image = self.preprocess_image(image, **preprocessing_options)
            
            # Extract text with boxes
            ocr_results = self.extract_text_with_boxes(processed_image)
            
            # Add metadata
            ocr_results.update({
                'original_image': original_image,
                'processed_image': processed_image,
                'file_type': file_type,
                'preprocessing_options': preprocessing_options,
                'processing_timestamp': datetime.now().isoformat()
            })
            
            return ocr_results
            
        except Exception as e:
            logging.error(f"Document processing failed: {e}")
            raise