"""
Generate a sample receipt image for testing the Document Intelligence system
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_receipt():
    """Create a sample receipt image for testing"""
    
    # Create image
    width, height = 400, 600
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    y_pos = 20
    
    # Store header
    draw.text((20, y_pos), "TECH MART ELECTRONICS", fill='black', font=font_large)
    y_pos += 30
    draw.text((20, y_pos), "123 Innovation Drive", fill='black', font=font_small)
    y_pos += 20
    draw.text((20, y_pos), "Silicon Valley, CA 94301", fill='black', font=font_small)
    y_pos += 20
    draw.text((20, y_pos), "Phone: (555) 123-4567", fill='black', font=font_small)
    y_pos += 40
    
    # Date and receipt info
    draw.text((20, y_pos), "Date: 03/15/2024", fill='black', font=font_medium)
    draw.text((250, y_pos), "Receipt #: 001234", fill='black', font=font_small)
    y_pos += 30
    
    # Separator line
    draw.line([(20, y_pos), (380, y_pos)], fill='black', width=1)
    y_pos += 20
    
    # Items
    items = [
        ("Wireless Bluetooth Speaker", 89.99),
        ("USB-C Cable (6ft)", 19.99),
        ("Phone Case Premium", 24.99),
        ("Screen Protector", 12.99)
    ]
    
    draw.text((20, y_pos), "ITEMS:", fill='black', font=font_medium)
    y_pos += 25
    
    total_before_tax = 0
    for item, price in items:
        draw.text((20, y_pos), item, fill='black', font=font_small)
        draw.text((300, y_pos), f"${price:.2f}", fill='black', font=font_small)
        total_before_tax += price
        y_pos += 20
    
    y_pos += 20
    
    # Subtotal, tax, total
    draw.line([(20, y_pos), (380, y_pos)], fill='black', width=1)
    y_pos += 15
    
    draw.text((20, y_pos), "SUBTOTAL:", fill='black', font=font_medium)
    draw.text((300, y_pos), f"${total_before_tax:.2f}", fill='black', font=font_medium)
    y_pos += 25
    
    tax_amount = total_before_tax * 0.0875  # 8.75% tax
    draw.text((20, y_pos), "TAX (8.75%):", fill='black', font=font_medium)
    draw.text((300, y_pos), f"${tax_amount:.2f}", fill='black', font=font_medium)
    y_pos += 25
    
    total_amount = total_before_tax + tax_amount
    draw.text((20, y_pos), "TOTAL:", fill='black', font=font_large)
    draw.text((300, y_pos), f"${total_amount:.2f}", fill='black', font=font_large)
    y_pos += 40
    
    # Payment method
    draw.text((20, y_pos), "Payment: VISA ****1234", fill='black', font=font_small)
    y_pos += 25
    
    # Footer
    draw.text((20, y_pos), "Thank you for shopping with us!", fill='black', font=font_small)
    y_pos += 20
    draw.text((20, y_pos), "Return policy: 30 days with receipt", fill='black', font=font_small)
    
    return img

if __name__ == "__main__":
    # Create samples directory if it doesn't exist
    os.makedirs("samples", exist_ok=True)
    
    # Generate and save sample receipt
    receipt = create_sample_receipt()
    receipt.save("samples/sample_receipt_1.png")
    print("Sample receipt saved as samples/sample_receipt_1.png")