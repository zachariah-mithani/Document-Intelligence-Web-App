"""
Streamlit Frontend for Document Intelligence Web App
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageDraw
import io
import json
import time
from typing import Dict, List, Optional
import requests
import base64

from ocr_processor import OCRProcessor
from field_extractor import FieldExtractor

# Configure Streamlit page
st.set_page_config(
    page_title="Document Intelligence Web App",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DocumentIntelligenceApp:
    def __init__(self):
        """Initialize the Streamlit application"""
        self.ocr_processor = OCRProcessor()
        self.field_extractor = FieldExtractor()
        
        # Initialize session state
        if 'processed_results' not in st.session_state:
            st.session_state.processed_results = None
        if 'original_image' not in st.session_state:
            st.session_state.original_image = None
        if 'processing_time' not in st.session_state:
            st.session_state.processing_time = 0
    
    def render_header(self):
        """Render application header"""
        st.title("📄 Document Intelligence Web App")
        st.markdown("""
        **Advanced OCR-powered receipt and invoice processing system**
        
        Upload a document (PNG, JPG, or PDF) to extract structured fields like vendor, date, and amounts.
        """)
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        st.sidebar.header("⚙️ Processing Options")
        
        # Preprocessing controls
        st.sidebar.subheader("Image Preprocessing")
        preprocessing_options = {
            'grayscale': st.sidebar.checkbox("Convert to Grayscale", value=True),
            'denoise': st.sidebar.checkbox("Reduce Noise", value=True),
            'deskew': st.sidebar.checkbox("Correct Skew", value=True),
            'upscale': st.sidebar.checkbox("Upscale Image", value=True),
            'binarize': st.sidebar.checkbox("Apply Binarization", value=True)
        }
        
        # OCR settings
        st.sidebar.subheader("OCR Settings")
        confidence_threshold = st.sidebar.slider(
            "Confidence Threshold",
            min_value=0,
            max_value=100,
            value=30,
            help="Minimum confidence score for text detection"
        )
        
        return preprocessing_options, confidence_threshold
    
    def render_file_upload(self):
        """Render file upload interface"""
        st.header("📤 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a document file",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Upload a PNG, JPG, or PDF document for processing"
        )
        
        return uploaded_file
    
    def process_document(self, uploaded_file, preprocessing_options, confidence_threshold):
        """Process uploaded document"""
        if uploaded_file is None:
            return False
        
        try:
            # Update OCR processor confidence threshold
            self.ocr_processor.confidence_threshold = confidence_threshold
            
            # Read file
            file_bytes = uploaded_file.read()
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            # Process document
            start_time = time.time()
            
            with st.spinner("🔄 Processing document..."):
                # OCR processing
                ocr_results = self.ocr_processor.process_document(
                    file_bytes, file_type, preprocessing_options
                )
                
                # Field extraction
                extracted_fields = self.field_extractor.extract_all_fields(ocr_results)
                
                # Combine results
                results = {
                    'ocr_results': ocr_results,
                    'extracted_fields': extracted_fields,
                    'file_info': {
                        'name': uploaded_file.name,
                        'size': len(file_bytes),
                        'type': file_type
                    }
                }
                
                processing_time = time.time() - start_time
                
                # Store in session state
                st.session_state.processed_results = results
                st.session_state.original_image = ocr_results['original_image']
                st.session_state.processing_time = processing_time
                
            st.success(f"✅ Document processed successfully in {processing_time:.2f} seconds!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
            return False
    
    def render_results(self):
        """Render processing results"""
        if st.session_state.processed_results is None:
            st.info("👆 Upload a document to see results here")
            return
        
        results = st.session_state.processed_results
        ocr_results = results['ocr_results']
        extracted_fields = results['extracted_fields']
        
        # Metrics
        st.header("📊 Processing Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Words Detected", ocr_results['word_count'])
        with col2:
            st.metric("Avg Confidence", f"{ocr_results['avg_confidence']:.1f}%")
        with col3:
            st.metric("Processing Time", f"{st.session_state.processing_time:.2f}s")
        with col4:
            st.metric("Overall Confidence", f"{extracted_fields['overall_confidence']:.1%}")
        
        # Extracted Fields
        st.header("🏷️ Extracted Fields")
        
        field_col1, field_col2 = st.columns(2)
        
        with field_col1:
            st.subheader("Business Information")
            vendor = extracted_fields['vendor'] or "Not found"
            date = extracted_fields['date'] or "Not found"
            
            st.write(f"**Vendor:** {vendor}")
            st.write(f"**Date:** {date}")
        
        with field_col2:
            st.subheader("Financial Information")
            subtotal = extracted_fields['subtotal']
            tax = extracted_fields['tax']
            total = extracted_fields['total']
            
            st.write(f"**Subtotal:** ${subtotal:.2f}" if subtotal else "**Subtotal:** Not found")
            st.write(f"**Tax:** ${tax:.2f}" if tax else "**Tax:** Not found")
            st.write(f"**Total:** ${total:.2f}" if total else "**Total:** Not found")
        
        # Visual Preview
        st.header("👁️ Visual Preview")
        self.render_visual_preview(ocr_results, extracted_fields)
        
        # Raw Data
        st.header("📋 Raw OCR Data")
        
        with st.expander("View Raw Text"):
            st.text_area("Extracted Text", ocr_results['text'], height=200)
        
        # Export Options
        st.header("💾 Export Data")
        self.render_export_options(results)
    
    def render_visual_preview(self, ocr_results, extracted_fields):
        """Render visual preview with highlighted text"""
        try:
            # Create image with bounding boxes
            image = ocr_results['original_image'].copy()
            if len(image.shape) == 3:
                image_pil = Image.fromarray(image)
            else:
                image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_GRAY2RGB))
            
            draw = ImageDraw.Draw(image_pil)
            
            # Draw all detected words
            confidence_threshold = st.slider(
                "Confidence Threshold for Visualization",
                min_value=0,
                max_value=100,
                value=30,
                key="viz_confidence"
            )
            
            words = ocr_results['words']
            boxes = ocr_results['boxes']
            confidences = ocr_results['confidences']
            
            # Draw word boxes
            for i, (word, box, conf) in enumerate(zip(words, boxes, confidences)):
                if conf >= confidence_threshold:
                    x1, y1, x2, y2 = box
                    
                    # Color based on confidence
                    if conf >= 80:
                        color = (0, 255, 0)  # Green for high confidence
                    elif conf >= 60:
                        color = (255, 255, 0)  # Yellow for medium confidence
                    else:
                        color = (255, 0, 0)  # Red for low confidence
                    
                    draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Highlight extracted fields
            field_details = extracted_fields['field_details']
            
            # Highlight vendor
            if field_details['vendor']['box']:
                box = field_details['vendor']['box']
                draw.rectangle(box, outline=(255, 0, 255), width=4)  # Magenta for vendor
            
            # Highlight date
            if field_details['date']['box']:
                box = field_details['date']['box']
                draw.rectangle(box, outline=(0, 255, 255), width=4)  # Cyan for date
            
            # Highlight amounts
            for amount_type, amount_data in field_details['amounts'].items():
                if amount_data['box']:
                    box = amount_data['box']
                    if amount_type == 'total':
                        draw.rectangle(box, outline=(255, 165, 0), width=4)  # Orange for total
                    else:
                        draw.rectangle(box, outline=(128, 0, 128), width=3)  # Purple for subtotal/tax
            
            # Display image
            st.image(image_pil, caption="Document with Detected Text and Extracted Fields", use_column_width=True)
            
            # Legend
            st.markdown("""
            **Legend:**
            - 🟢 Green: High confidence text (80%+)
            - 🟡 Yellow: Medium confidence text (60-80%)
            - 🔴 Red: Low confidence text (<60%)
            - 🟣 Magenta: Vendor name
            - 🟦 Cyan: Date
            - 🟠 Orange: Total amount
            - 🟪 Purple: Subtotal/Tax
            """)
            
        except Exception as e:
            st.error(f"Error creating visual preview: {str(e)}")
    
    def render_export_options(self, results):
        """Render export options"""
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON Export
            if st.button("📄 Download JSON"):
                json_data = {
                    'extracted_fields': results['extracted_fields'],
                    'raw_text': results['ocr_results']['text'],
                    'word_count': results['ocr_results']['word_count'],
                    'avg_confidence': results['ocr_results']['avg_confidence'],
                    'processing_timestamp': results['extracted_fields']['extraction_timestamp']
                }
                
                json_str = json.dumps(json_data, indent=2)
                st.download_button(
                    label="Download JSON Report",
                    data=json_str,
                    file_name=f"document_intelligence_{int(time.time())}.json",
                    mime="application/json"
                )
        
        with col2:
            # CSV Export (simplified)
            if st.button("📊 Download CSV"):
                csv_data = f"""Field,Value,Confidence
Vendor,{results['extracted_fields']['vendor'] or 'N/A'},{results['extracted_fields']['field_details']['vendor']['confidence']:.2%}
Date,{results['extracted_fields']['date'] or 'N/A'},{results['extracted_fields']['field_details']['date']['confidence']:.2%}
Subtotal,{results['extracted_fields']['subtotal'] or 'N/A'},{results['extracted_fields']['field_details']['amounts']['subtotal']['confidence']:.2%}
Tax,{results['extracted_fields']['tax'] or 'N/A'},{results['extracted_fields']['field_details']['amounts']['tax']['confidence']:.2%}
Total,{results['extracted_fields']['total'] or 'N/A'},{results['extracted_fields']['field_details']['amounts']['total']['confidence']:.2%}
"""
                
                st.download_button(
                    label="Download CSV Report",
                    data=csv_data,
                    file_name=f"document_intelligence_{int(time.time())}.csv",
                    mime="text/csv"
                )
    
    def run(self):
        """Main application entry point"""
        self.render_header()
        
        # Sidebar controls
        preprocessing_options, confidence_threshold = self.render_sidebar()
        
        # File upload
        uploaded_file = self.render_file_upload()
        
        # Process button
        if st.button("🚀 Run Extraction", type="primary", disabled=(uploaded_file is None)):
            self.process_document(uploaded_file, preprocessing_options, confidence_threshold)
        
        # Results
        self.render_results()

def main():
    """Main function"""
    app = DocumentIntelligenceApp()
    app.run()

if __name__ == "__main__":
    main()