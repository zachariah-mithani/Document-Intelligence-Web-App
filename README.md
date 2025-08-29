# 📄 Document Intelligence

An intelligent document analysis assistant that extracts structured data from receipts and invoices. It performs OCR, parses key fields, and generates exportable reports. Designed for compliance, automation, and real-world business workflows.

---

## Features
- **OCR-based text extraction** from images & PDFs (receipts, invoices)  
- **Key field parsing**: vendor, date, subtotal, tax, and total  
- **Preprocessing pipeline** (deskew, denoise, binarize) for cleaner recognition  
- **Visual overlay preview** with detected text boxes & highlighted fields  
- **Exportable outputs** (JSON, CSV for line items, annotated images)  
- **Rule-based validation** (subtotal + tax ≈ total)  
- **REST API** (`/ocr`, `/extract`) for integration into other systems  
- **Sample evaluation harness** with metrics (accuracy, latency)  
- **Modern UI** (Streamlit) with parameter controls & live previews  

---

## Tech Stack
- **Frontend/UI:** Streamlit  
- **Backend API:** FastAPI  
- **OCR Engine:** Tesseract (pytesseract) / PaddleOCR  
- **Preprocessing:** OpenCV (deskew, denoise, binarize)  
- **PDF Handling:** pdf2image, Camelot (optional for tables)  
- **Exports:** JSON, CSV, annotated images  

---

##  Preview
<img width="603" height="776" alt="Screenshot 2025-08-29 at 3 45 18 AM" src="https://github.com/user-attachments/assets/a15572fb-4487-4fd6-bfca-9e125e2cea29" />

