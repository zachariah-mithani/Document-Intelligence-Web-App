"""
FastAPI Backend for Document Intelligence Web App
Provides REST API endpoints for OCR and field extraction
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from typing import Dict, Optional
import io
from datetime import datetime

from ocr_processor import OCRProcessor
from field_extractor import FieldExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Intelligence API",
    description="OCR-powered document processing with field extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
ocr_processor = OCRProcessor()
field_extractor = FieldExtractor()

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "document-intelligence-api",
        "version": "1.0.0"
    }

@app.post("/ocr")
async def extract_ocr(
    file: UploadFile = File(...),
    grayscale: bool = Form(True),
    denoise: bool = Form(True),
    deskew: bool = Form(True),
    upscale: bool = Form(True),
    binarize: bool = Form(True),
    confidence_threshold: int = Form(30)
):
    """
    Extract raw OCR text and bounding boxes from document
    
    Args:
        file: Uploaded document file (PNG, JPG, PDF)
        grayscale: Apply grayscale conversion
        denoise: Apply noise reduction
        deskew: Correct image skew
        upscale: Upscale image for better OCR
        binarize: Apply binary thresholding
        confidence_threshold: Minimum confidence for text detection
        
    Returns:
        Raw OCR results with text, boxes, and confidence scores
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['png', 'jpg', 'jpeg', 'pdf']:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PNG, JPG, or PDF files."
            )
        
        # Read file contents
        file_contents = await file.read()
        
        # Configure preprocessing options
        preprocessing_options = {
            'grayscale': grayscale,
            'denoise': denoise,
            'deskew': deskew,
            'upscale': upscale,
            'binarize': binarize
        }
        
        # Update confidence threshold
        ocr_processor.confidence_threshold = confidence_threshold
        
        # Process document
        logger.info(f"Processing OCR for file: {file.filename}")
        ocr_results = ocr_processor.process_document(
            file_contents, file_extension, preprocessing_options
        )
        
        processing_time = time.time() - start_time
        
        # Prepare response (exclude image arrays for JSON serialization)
        response = {
            "text": ocr_results['text'],
            "words": ocr_results['words'],
            "boxes": ocr_results['boxes'],
            "confidences": ocr_results['confidences'],
            "word_count": ocr_results['word_count'],
            "avg_confidence": ocr_results['avg_confidence'],
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "size_bytes": len(file_contents)
            },
            "processing_info": {
                "preprocessing_options": preprocessing_options,
                "confidence_threshold": confidence_threshold,
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"OCR completed in {processing_time:.3f}s for {file.filename}")
        return response
        
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/extract")
async def extract_fields(
    file: UploadFile = File(...),
    grayscale: bool = Form(True),
    denoise: bool = Form(True),
    deskew: bool = Form(True),
    upscale: bool = Form(True),
    binarize: bool = Form(True),
    confidence_threshold: int = Form(30)
):
    """
    Complete document processing pipeline with field extraction
    
    Args:
        file: Uploaded document file (PNG, JPG, PDF)
        grayscale: Apply grayscale conversion
        denoise: Apply noise reduction
        deskew: Correct image skew
        upscale: Upscale image for better OCR
        binarize: Apply binary thresholding
        confidence_threshold: Minimum confidence for text detection
        
    Returns:
        Extracted fields (vendor, date, amounts) with OCR data and confidence scores
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['png', 'jpg', 'jpeg', 'pdf']:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PNG, JPG, or PDF files."
            )
        
        # Read file contents
        file_contents = await file.read()
        
        # Configure preprocessing options
        preprocessing_options = {
            'grayscale': grayscale,
            'denoise': denoise,
            'deskew': deskew,
            'upscale': upscale,
            'binarize': binarize
        }
        
        # Update confidence threshold
        ocr_processor.confidence_threshold = confidence_threshold
        
        # Process document with OCR
        logger.info(f"Processing complete extraction for file: {file.filename}")
        ocr_results = ocr_processor.process_document(
            file_contents, file_extension, preprocessing_options
        )
        
        # Extract structured fields
        extracted_fields = field_extractor.extract_all_fields(ocr_results)
        
        processing_time = time.time() - start_time
        
        # Prepare comprehensive response
        response = {
            "extracted_fields": {
                "vendor": extracted_fields['vendor'],
                "date": extracted_fields['date'],
                "subtotal": extracted_fields['subtotal'],
                "tax": extracted_fields['tax'],
                "total": extracted_fields['total'],
                "overall_confidence": extracted_fields['overall_confidence']
            },
            "field_details": extracted_fields['field_details'],
            "ocr_data": {
                "text": ocr_results['text'],
                "words": ocr_results['words'],
                "boxes": ocr_results['boxes'],
                "confidences": ocr_results['confidences'],
                "word_count": ocr_results['word_count'],
                "avg_confidence": ocr_results['avg_confidence']
            },
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "size_bytes": len(file_contents)
            },
            "processing_info": {
                "preprocessing_options": preprocessing_options,
                "confidence_threshold": confidence_threshold,
                "processing_time_seconds": round(processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Complete extraction completed in {processing_time:.3f}s for {file.filename}")
        return response
        
    except Exception as e:
        logger.error(f"Field extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Field extraction failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Document Intelligence API",
        "version": "1.0.0",
        "description": "OCR-powered document processing with intelligent field extraction",
        "endpoints": {
            "/healthz": "Health check",
            "/ocr": "Extract raw OCR text and bounding boxes",
            "/extract": "Complete document processing with field extraction",
            "/docs": "Interactive API documentation"
        },
        "supported_formats": ["PNG", "JPG", "JPEG", "PDF"],
        "features": [
            "Advanced image preprocessing",
            "Tesseract OCR integration",
            "Intelligent field extraction",
            "Confidence scoring",
            "Visual bounding boxes"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)