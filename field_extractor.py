"""
Field Extraction Module for Document Intelligence
Extracts structured fields from OCR text using pattern matching and NLP
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dateutil import parser as date_parser
import numpy as np

class FieldExtractor:
    def __init__(self):
        """Initialize field extractor with patterns and configurations"""
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b',    # MM/DD/YY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',   # DD Month YYYY
        ]
        
        self.currency_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',  # 1,234.56$
            r'\$\d+(?:\.\d{2})?',                     # $123.45
            r'\d+(?:\.\d{2})?',                       # 123.45 (fallback)
        ]
        
        self.amount_keywords = {
            'subtotal': ['subtotal', 'sub total', 'sub-total', 'amount before tax', 'net amount'],
            'tax': ['tax', 'sales tax', 'vat', 'gst', 'hst', 'tax amount'],
            'total': ['total', 'amount due', 'total amount', 'grand total', 'balance due', 'total due']
        }
        
        self.vendor_stop_words = {
            'receipt', 'invoice', 'bill', 'statement', 'order', 'purchase', 'sale',
            'date', 'time', 'total', 'tax', 'subtotal', 'amount', 'due', 'paid',
            'cash', 'credit', 'card', 'visa', 'mastercard', 'amex', 'discover'
        }
    
    def extract_dates(self, text: str, words: List[str], boxes: List[Tuple], confidences: List[float]) -> Dict:
        """Extract date information from text"""
        found_dates = []
        date_boxes = []
        
        # Search for date patterns
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group()
                try:
                    # Parse and validate date
                    parsed_date = date_parser.parse(date_str, fuzzy=True)
                    
                    # Validate date range (reasonable for receipts/invoices)
                    if 2000 <= parsed_date.year <= datetime.now().year + 1:
                        # Find corresponding box
                        box = self._find_text_box(date_str, words, boxes)
                        confidence = self._calculate_field_confidence(date_str, words, confidences)
                        
                        found_dates.append({
                            'raw_text': date_str,
                            'parsed_date': parsed_date.strftime('%Y-%m-%d'),
                            'confidence': confidence,
                            'box': box
                        })
                except:
                    continue
        
        # Return best date (highest confidence)
        if found_dates:
            best_date = max(found_dates, key=lambda x: x['confidence'])
            return {
                'date': best_date['parsed_date'],
                'raw_text': best_date['raw_text'],
                'confidence': best_date['confidence'],
                'box': best_date['box']
            }
        
        return {'date': None, 'raw_text': '', 'confidence': 0, 'box': None}
    
    def extract_amounts(self, text: str, words: List[str], boxes: List[Tuple], confidences: List[float]) -> Dict:
        """Extract monetary amounts (subtotal, tax, total)"""
        amounts = {
            'subtotal': {'amount': None, 'confidence': 0, 'box': None, 'raw_text': ''},
            'tax': {'amount': None, 'confidence': 0, 'box': None, 'raw_text': ''},
            'total': {'amount': None, 'confidence': 0, 'box': None, 'raw_text': ''}
        }
        
        lines = text.split('\n')
        
        for amount_type, keywords in self.amount_keywords.items():
            best_match = {'amount': None, 'confidence': 0, 'box': None, 'raw_text': ''}
            
            for line in lines:
                line = line.strip().lower()
                
                # Check if line contains any keyword for this amount type
                for keyword in keywords:
                    if keyword in line:
                        # Extract currency amount from this line
                        amount_match = self._extract_currency_from_line(line, words, boxes, confidences)
                        
                        if amount_match and amount_match['confidence'] > best_match['confidence']:
                            best_match = amount_match
                            break
            
            amounts[amount_type] = best_match
        
        # Validate amounts (subtotal + tax ≈ total)
        amounts = self._validate_amounts(amounts)
        
        return amounts
    
    def extract_vendor(self, text: str, words: List[str], boxes: List[Tuple], confidences: List[float]) -> Dict:
        """Extract vendor/company name"""
        lines = text.split('\n')
        vendor_candidates = []
        
        # Look for vendor in top portion of document
        top_lines = lines[:min(10, len(lines))]
        
        for i, line in enumerate(top_lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are clearly not vendor names
            if self._is_vendor_candidate(line):
                # Calculate confidence based on position, length, and OCR confidence
                position_score = (10 - i) / 10  # Higher score for lines near top
                length_score = min(len(line) / 50, 1)  # Reasonable length
                
                # Find OCR confidence for this line
                ocr_confidence = self._calculate_field_confidence(line, words, confidences)
                
                overall_confidence = (position_score * 0.4 + length_score * 0.2 + ocr_confidence * 0.4)
                
                box = self._find_text_box(line, words, boxes)
                
                vendor_candidates.append({
                    'vendor': line.title(),
                    'confidence': overall_confidence,
                    'box': box,
                    'raw_text': line
                })
        
        # Return best vendor candidate
        if vendor_candidates:
            best_vendor = max(vendor_candidates, key=lambda x: x['confidence'])
            return best_vendor
        
        return {'vendor': None, 'confidence': 0, 'box': None, 'raw_text': ''}
    
    def _extract_currency_from_line(self, line: str, words: List[str], boxes: List[Tuple], confidences: List[float]) -> Optional[Dict]:
        """Extract currency amount from a text line"""
        for pattern in self.currency_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                amount_str = match.group()
                try:
                    # Clean and parse amount
                    clean_amount = re.sub(r'[^\d.]', '', amount_str)
                    amount = float(clean_amount)
                    
                    if amount > 0:  # Valid positive amount
                        box = self._find_text_box(amount_str, words, boxes)
                        confidence = self._calculate_field_confidence(amount_str, words, confidences)
                        
                        return {
                            'amount': amount,
                            'raw_text': amount_str,
                            'confidence': confidence,
                            'box': box
                        }
                except:
                    continue
        return None
    
    def _is_vendor_candidate(self, line: str) -> bool:
        """Check if a line could be a vendor name"""
        line_lower = line.lower()
        
        # Skip if contains common non-vendor words
        for stop_word in self.vendor_stop_words:
            if stop_word in line_lower:
                return False
        
        # Skip if mostly numbers
        if len(re.sub(r'[^\d]', '', line)) > len(line) * 0.5:
            return False
        
        # Must have reasonable length
        if len(line.strip()) < 3 or len(line.strip()) > 100:
            return False
        
        return True
    
    def _find_text_box(self, text: str, words: List[str], boxes: List[Tuple]) -> Optional[Tuple]:
        """Find bounding box for a piece of text"""
        text = text.strip().lower()
        
        for i, word in enumerate(words):
            if word.lower() in text or text in word.lower():
                return boxes[i]
        
        return None
    
    def _calculate_field_confidence(self, text: str, words: List[str], confidences: List[float]) -> float:
        """Calculate confidence score for extracted field"""
        text_words = text.lower().split()
        matching_confidences = []
        
        for word in text_words:
            for i, ocr_word in enumerate(words):
                if word in ocr_word.lower() or ocr_word.lower() in word:
                    matching_confidences.append(confidences[i])
        
        if matching_confidences:
            return float(np.mean(matching_confidences)) / 100  # Normalize to 0-1
        
        return 0.5  # Default confidence
    
    def _validate_amounts(self, amounts: Dict) -> Dict:
        """Validate extracted amounts using business logic"""
        subtotal = amounts['subtotal']['amount']
        tax = amounts['tax']['amount']
        total = amounts['total']['amount']
        
        if subtotal and tax and total:
            expected_total = subtotal + tax
            tolerance = max(0.02, total * 0.01)  # 1% tolerance or $0.02 minimum
            
            if abs(total - expected_total) <= tolerance:
                # Amounts are consistent, boost confidence
                for amount_type in amounts:
                    amounts[amount_type]['confidence'] = min(1.0, amounts[amount_type]['confidence'] + 0.2)
            else:
                # Amounts inconsistent, reduce confidence
                for amount_type in amounts:
                    amounts[amount_type]['confidence'] = max(0.0, amounts[amount_type]['confidence'] - 0.3)
        
        return amounts
    
    def extract_all_fields(self, ocr_results: Dict) -> Dict:
        """Extract all structured fields from OCR results"""
        text = ocr_results['text']
        words = ocr_results['words']
        boxes = ocr_results['boxes']
        confidences = ocr_results['confidences']
        
        # Extract each field type
        date_info = self.extract_dates(text, words, boxes, confidences)
        amounts_info = self.extract_amounts(text, words, boxes, confidences)
        vendor_info = self.extract_vendor(text, words, boxes, confidences)
        
        # Compile results
        extracted_fields = {
            'vendor': vendor_info['vendor'],
            'date': date_info['date'],
            'subtotal': amounts_info['subtotal']['amount'],
            'tax': amounts_info['tax']['amount'],
            'total': amounts_info['total']['amount'],
            
            # Detailed information
            'field_details': {
                'vendor': vendor_info,
                'date': date_info,
                'amounts': amounts_info
            },
            
            # Overall confidence
            'overall_confidence': np.mean([
                vendor_info['confidence'],
                date_info['confidence'],
                amounts_info['subtotal']['confidence'],
                amounts_info['tax']['confidence'],
                amounts_info['total']['confidence']
            ]),
            
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        return extracted_fields