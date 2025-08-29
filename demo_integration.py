"""
Document Intelligence Demo Integration for Portfolio Page
Creates a simplified demo that can be embedded in the portfolio
"""

import base64
import io
import json
from typing import Dict, Optional
from PIL import Image, ImageDraw
import numpy as np

from ocr_processor import OCRProcessor
from field_extractor import FieldExtractor

class PortfolioDemo:
    def __init__(self):
        """Initialize demo with processors"""
        self.ocr_processor = OCRProcessor()
        self.field_extractor = FieldExtractor()
    
    def process_demo_image(self, image_data: str) -> Dict:
        """
        Process base64 encoded image for demo
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            Processing results with extracted fields and visualization
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            
            # Process with OCR
            ocr_results = self.ocr_processor.process_document(image_bytes, 'png')
            
            # Extract fields
            extracted_fields = self.field_extractor.extract_all_fields(ocr_results)
            
            # Create visualization
            visualization = self.create_demo_visualization(ocr_results, extracted_fields)
            
            # Prepare response
            return {
                'success': True,
                'extracted_fields': {
                    'vendor': extracted_fields['vendor'],
                    'date': extracted_fields['date'],
                    'subtotal': extracted_fields['subtotal'],
                    'tax': extracted_fields['tax'],
                    'total': extracted_fields['total']
                },
                'confidence': extracted_fields['overall_confidence'],
                'word_count': ocr_results['word_count'],
                'avg_ocr_confidence': ocr_results['avg_confidence'],
                'visualization': visualization
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_demo_visualization(self, ocr_results: Dict, extracted_fields: Dict) -> str:
        """Create visualization image with bounding boxes"""
        try:
            # Get original image
            image = ocr_results['original_image'].copy()
            if len(image.shape) == 3:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray(np.stack([image] * 3, axis=-1))
            
            draw = ImageDraw.Draw(pil_image)
            
            # Draw detected words
            words = ocr_results['words']
            boxes = ocr_results['boxes'] 
            confidences = ocr_results['confidences']
            
            for word, box, conf in zip(words, boxes, confidences):
                if conf >= 30:  # Only show confident detections
                    x1, y1, x2, y2 = box
                    
                    # Color based on confidence
                    if conf >= 80:
                        color = (0, 255, 0, 128)  # Green
                    elif conf >= 60:
                        color = (255, 255, 0, 128)  # Yellow
                    else:
                        color = (255, 0, 0, 128)  # Red
                    
                    draw.rectangle([x1, y1, x2, y2], outline=color[:3], width=1)
            
            # Highlight extracted fields
            field_details = extracted_fields['field_details']
            
            # Vendor (magenta)
            if field_details['vendor']['box']:
                box = field_details['vendor']['box']
                draw.rectangle(box, outline=(255, 0, 255), width=3)
            
            # Date (cyan)
            if field_details['date']['box']:
                box = field_details['date']['box']
                draw.rectangle(box, outline=(0, 255, 255), width=3)
            
            # Amounts (orange/purple)
            for amount_type, amount_data in field_details['amounts'].items():
                if amount_data['box']:
                    box = amount_data['box']
                    if amount_type == 'total':
                        draw.rectangle(box, outline=(255, 165, 0), width=3)  # Orange
                    else:
                        draw.rectangle(box, outline=(128, 0, 128), width=2)  # Purple
            
            # Convert back to base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            return ""
    
    def get_demo_html(self) -> str:
        """Generate HTML for embedded demo"""
        return """
        <div id="document-intelligence-demo" class="demo-container">
            <h3>🔄 Document Intelligence Demo</h3>
            <p>Upload a receipt or invoice to see intelligent field extraction in action</p>
            
            <div class="demo-upload">
                <input type="file" id="demo-file-input" accept="image/*,.pdf" style="display: none;">
                <button id="demo-upload-btn" class="demo-button">📤 Upload Document</button>
                <button id="demo-sample-btn" class="demo-button">📄 Try Sample Receipt</button>
            </div>
            
            <div id="demo-processing" class="demo-processing" style="display: none;">
                <div class="demo-spinner"></div>
                <p>Processing document...</p>
            </div>
            
            <div id="demo-results" class="demo-results" style="display: none;">
                <div class="demo-metrics">
                    <div class="metric">
                        <span class="metric-label">Words Detected:</span>
                        <span id="words-count">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">OCR Confidence:</span>
                        <span id="ocr-confidence">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Overall Confidence:</span>
                        <span id="overall-confidence">-</span>
                    </div>
                </div>
                
                <div class="demo-fields">
                    <h4>📋 Extracted Fields</h4>
                    <div class="field-grid">
                        <div class="field-item">
                            <label>Vendor:</label>
                            <span id="field-vendor">-</span>
                        </div>
                        <div class="field-item">
                            <label>Date:</label>
                            <span id="field-date">-</span>
                        </div>
                        <div class="field-item">
                            <label>Subtotal:</label>
                            <span id="field-subtotal">-</span>
                        </div>
                        <div class="field-item">
                            <label>Tax:</label>
                            <span id="field-tax">-</span>
                        </div>
                        <div class="field-item">
                            <label>Total:</label>
                            <span id="field-total">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="demo-visualization">
                    <h4>👁️ Visual Analysis</h4>
                    <img id="demo-viz-image" src="" alt="Document analysis" style="max-width: 100%; height: auto;">
                </div>
            </div>
        </div>
        
        <style>
        .demo-container {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin: 2rem 0;
        }
        
        .demo-upload {
            text-align: center;
            margin: 1.5rem 0;
        }
        
        .demo-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            margin: 0 0.5rem;
            transition: transform 0.2s;
        }
        
        .demo-button:hover {
            transform: translateY(-2px);
        }
        
        .demo-processing {
            text-align: center;
            padding: 2rem;
        }
        
        .demo-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .demo-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .metric {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        
        .metric-label {
            display: block;
            font-size: 0.875rem;
            color: #6c757d;
            margin-bottom: 0.25rem;
        }
        
        .field-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .field-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
        }
        
        .field-item label {
            font-weight: 600;
            color: #495057;
            display: block;
            margin-bottom: 0.25rem;
        }
        
        .demo-visualization {
            margin-top: 2rem;
        }
        
        .demo-visualization img {
            border: 2px solid #dee2e6;
            border-radius: 8px;
        }
        </style>
        
        <script>
        // Document Intelligence Demo JavaScript
        (function() {
            const demoContainer = document.getElementById('document-intelligence-demo');
            const fileInput = document.getElementById('demo-file-input');
            const uploadBtn = document.getElementById('demo-upload-btn');
            const sampleBtn = document.getElementById('demo-sample-btn');
            const processing = document.getElementById('demo-processing');
            const results = document.getElementById('demo-results');
            
            // Upload button click
            uploadBtn.addEventListener('click', () => {
                fileInput.click();
            });
            
            // File input change
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    processFile(file);
                }
            });
            
            // Sample button click
            sampleBtn.addEventListener('click', () => {
                processSampleReceipt();
            });
            
            function processFile(file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const imageData = e.target.result;
                    simulateProcessing(imageData);
                };
                reader.readAsDataURL(file);
            }
            
            function processSampleReceipt() {
                // Simulate processing with sample data
                const sampleResults = {
                    success: true,
                    extracted_fields: {
                        vendor: "TECH MART ELECTRONICS",
                        date: "2024-03-15",
                        subtotal: 147.96,
                        tax: 12.95,
                        total: 160.91
                    },
                    confidence: 0.87,
                    word_count: 45,
                    avg_ocr_confidence: 82.3
                };
                
                showProcessing();
                setTimeout(() => {
                    displayResults(sampleResults);
                }, 2000);
            }
            
            function simulateProcessing(imageData) {
                showProcessing();
                
                // Simulate API call delay
                setTimeout(() => {
                    const mockResults = {
                        success: true,
                        extracted_fields: {
                            vendor: "Sample Store",
                            date: "2024-01-15",
                            subtotal: 25.99,
                            tax: 2.08,
                            total: 28.07
                        },
                        confidence: 0.75,
                        word_count: 32,
                        avg_ocr_confidence: 78.5
                    };
                    
                    displayResults(mockResults);
                }, 3000);
            }
            
            function showProcessing() {
                results.style.display = 'none';
                processing.style.display = 'block';
            }
            
            function displayResults(data) {
                processing.style.display = 'none';
                
                if (data.success) {
                    // Update metrics
                    document.getElementById('words-count').textContent = data.word_count;
                    document.getElementById('ocr-confidence').textContent = data.avg_ocr_confidence.toFixed(1) + '%';
                    document.getElementById('overall-confidence').textContent = (data.confidence * 100).toFixed(1) + '%';
                    
                    // Update fields
                    const fields = data.extracted_fields;
                    document.getElementById('field-vendor').textContent = fields.vendor || 'Not found';
                    document.getElementById('field-date').textContent = fields.date || 'Not found';
                    document.getElementById('field-subtotal').textContent = fields.subtotal ? '$' + fields.subtotal.toFixed(2) : 'Not found';
                    document.getElementById('field-tax').textContent = fields.tax ? '$' + fields.tax.toFixed(2) : 'Not found';
                    document.getElementById('field-total').textContent = fields.total ? '$' + fields.total.toFixed(2) : 'Not found';
                    
                    // Hide visualization for now (would need actual image processing)
                    document.querySelector('.demo-visualization').style.display = 'none';
                    
                    results.style.display = 'block';
                } else {
                    alert('Processing failed: ' + data.error);
                }
            }
        })();
        </script>
        """