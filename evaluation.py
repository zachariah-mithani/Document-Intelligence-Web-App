"""
Evaluation system for Document Intelligence accuracy testing
"""

import json
import os
from typing import Dict, List
import pandas as pd
from pathlib import Path

from ocr_processor import OCRProcessor
from field_extractor import FieldExtractor

class DocumentEvaluator:
    def __init__(self):
        """Initialize evaluator with ground truth data"""
        self.ocr_processor = OCRProcessor()
        self.field_extractor = FieldExtractor()
        
        # Ground truth data for sample documents
        self.ground_truth = {
            "sample_receipt_1.png": {
                "vendor": "TECH MART ELECTRONICS",
                "date": "2024-03-15",
                "subtotal": 147.96,
                "tax": 12.95,
                "total": 160.91,
                "expected_words_min": 30  # Minimum expected word count
            }
        }
    
    def evaluate_sample_documents(self) -> Dict:
        """Evaluate accuracy on sample documents"""
        results = {
            "overall_metrics": {
                "documents_processed": 0,
                "documents_successful": 0,
                "avg_field_accuracy": 0.0,
                "avg_ocr_confidence": 0.0
            },
            "document_results": {}
        }
        
        samples_dir = Path("samples")
        if not samples_dir.exists():
            return {"error": "Samples directory not found"}
        
        total_accuracy = 0
        total_confidence = 0
        successful_docs = 0
        
        for filename, expected in self.ground_truth.items():
            file_path = samples_dir / filename
            
            if not file_path.exists():
                print(f"⚠️ Sample file not found: {filename}")
                continue
            
            try:
                print(f"🔍 Evaluating {filename}...")
                
                # Process document
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                file_type = filename.split('.')[-1].lower()
                ocr_results = self.ocr_processor.process_document(file_bytes, file_type)
                extracted_fields = self.field_extractor.extract_all_fields(ocr_results)
                
                # Calculate accuracy metrics
                field_accuracy = self.calculate_field_accuracy(extracted_fields, expected)
                ocr_quality = self.calculate_ocr_quality(ocr_results, expected)
                
                # Store results
                doc_result = {
                    "filename": filename,
                    "field_accuracy": field_accuracy,
                    "ocr_quality": ocr_quality,
                    "extracted_fields": {
                        "vendor": extracted_fields['vendor'],
                        "date": extracted_fields['date'], 
                        "subtotal": extracted_fields['subtotal'],
                        "tax": extracted_fields['tax'],
                        "total": extracted_fields['total']
                    },
                    "expected_fields": expected,
                    "overall_confidence": extracted_fields['overall_confidence']
                }
                
                results["document_results"][filename] = doc_result
                
                total_accuracy += field_accuracy["overall_accuracy"]
                total_confidence += ocr_results['avg_confidence']
                successful_docs += 1
                
                print(f"✅ {filename}: {field_accuracy['overall_accuracy']:.1%} accuracy")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                results["document_results"][filename] = {"error": str(e)}
        
        # Calculate overall metrics
        if successful_docs > 0:
            results["overall_metrics"]["documents_processed"] = len(self.ground_truth)
            results["overall_metrics"]["documents_successful"] = successful_docs
            results["overall_metrics"]["avg_field_accuracy"] = total_accuracy / successful_docs
            results["overall_metrics"]["avg_ocr_confidence"] = total_confidence / successful_docs
        
        return results
    
    def calculate_field_accuracy(self, extracted: Dict, expected: Dict) -> Dict:
        """Calculate accuracy for extracted fields"""
        field_scores = {}
        
        # Vendor accuracy (fuzzy matching)
        vendor_score = 0.0
        if extracted['vendor'] and expected['vendor']:
            extracted_vendor = extracted['vendor'].upper().strip()
            expected_vendor = expected['vendor'].upper().strip()
            
            if extracted_vendor == expected_vendor:
                vendor_score = 1.0
            elif expected_vendor in extracted_vendor or extracted_vendor in expected_vendor:
                vendor_score = 0.7  # Partial match
        
        field_scores['vendor'] = vendor_score
        
        # Date accuracy (exact match)
        date_score = 0.0
        if extracted['date'] and expected['date']:
            if extracted['date'] == expected['date']:
                date_score = 1.0
        
        field_scores['date'] = date_score
        
        # Amount accuracy (with tolerance)
        for amount_field in ['subtotal', 'tax', 'total']:
            amount_score = 0.0
            extracted_amount = extracted[amount_field]
            expected_amount = expected[amount_field]
            
            if extracted_amount is not None and expected_amount is not None:
                tolerance = max(0.02, expected_amount * 0.01)  # 1% or $0.02
                if abs(extracted_amount - expected_amount) <= tolerance:
                    amount_score = 1.0
                elif abs(extracted_amount - expected_amount) <= tolerance * 2:
                    amount_score = 0.5  # Close but not exact
            
            field_scores[amount_field] = amount_score
        
        # Overall accuracy
        overall_accuracy = sum(field_scores.values()) / len(field_scores)
        
        return {
            "field_scores": field_scores,
            "overall_accuracy": overall_accuracy
        }
    
    def calculate_ocr_quality(self, ocr_results: Dict, expected: Dict) -> Dict:
        """Calculate OCR quality metrics"""
        return {
            "word_count": ocr_results['word_count'],
            "avg_confidence": ocr_results['avg_confidence'],
            "meets_word_threshold": ocr_results['word_count'] >= expected.get('expected_words_min', 20),
            "confidence_grade": "High" if ocr_results['avg_confidence'] >= 80 else 
                              "Medium" if ocr_results['avg_confidence'] >= 60 else "Low"
        }
    
    def generate_evaluation_report(self) -> str:
        """Generate a comprehensive evaluation report"""
        print("📊 Running Document Intelligence Evaluation...")
        print("=" * 60)
        
        results = self.evaluate_sample_documents()
        
        if "error" in results:
            return f"Evaluation failed: {results['error']}"
        
        # Generate report
        report = []
        report.append("📄 DOCUMENT INTELLIGENCE EVALUATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overall metrics
        metrics = results["overall_metrics"]
        report.append("📊 OVERALL METRICS:")
        report.append(f"   Documents Processed: {metrics['documents_processed']}")
        report.append(f"   Successful Extractions: {metrics['documents_successful']}")
        report.append(f"   Average Field Accuracy: {metrics['avg_field_accuracy']:.1%}")
        report.append(f"   Average OCR Confidence: {metrics['avg_ocr_confidence']:.1f}%")
        report.append("")
        
        # Document-by-document results
        report.append("📋 DOCUMENT RESULTS:")
        report.append("")
        
        for filename, doc_result in results["document_results"].items():
            if "error" in doc_result:
                report.append(f"❌ {filename}: {doc_result['error']}")
                continue
            
            report.append(f"📄 {filename}:")
            report.append(f"   Overall Accuracy: {doc_result['field_accuracy']['overall_accuracy']:.1%}")
            report.append(f"   OCR Confidence: {doc_result['overall_confidence']:.1%}")
            
            # Field-by-field comparison
            extracted = doc_result['extracted_fields']
            expected = doc_result['expected_fields']
            field_scores = doc_result['field_accuracy']['field_scores']
            
            report.append("   Field Extraction:")
            for field in ['vendor', 'date', 'subtotal', 'tax', 'total']:
                score = field_scores[field]
                status = "✅" if score >= 0.9 else "⚠️" if score >= 0.5 else "❌"
                
                extracted_val = extracted[field]
                expected_val = expected[field]
                
                if field in ['subtotal', 'tax', 'total']:
                    extracted_str = f"${extracted_val:.2f}" if extracted_val else "None"
                    expected_str = f"${expected_val:.2f}" if expected_val else "None"
                else:
                    extracted_str = str(extracted_val) if extracted_val else "None"
                    expected_str = str(expected_val) if expected_val else "None"
                
                report.append(f"     {status} {field.title()}: {extracted_str} (expected: {expected_str}) - {score:.1%}")
            
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        avg_accuracy = metrics['avg_field_accuracy']
        
        if avg_accuracy >= 0.9:
            report.append("   ✅ System performing excellently!")
        elif avg_accuracy >= 0.7:
            report.append("   ⚠️ Good performance, consider fine-tuning preprocessing parameters")
        else:
            report.append("   ❌ Performance needs improvement:")
            report.append("      - Check image quality and preprocessing steps")
            report.append("      - Review field extraction patterns")
            report.append("      - Consider additional training data")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """Run evaluation and print report"""
    evaluator = DocumentEvaluator()
    report = evaluator.generate_evaluation_report()
    print(report)
    
    # Save report to file
    with open("evaluation_report.txt", "w") as f:
        f.write(report)
    
    print(f"\n📁 Report saved to: evaluation_report.txt")

if __name__ == "__main__":
    main()