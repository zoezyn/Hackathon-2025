import fitz  # PyMuPDF
import os

def get_field_type_name(field_type):
    # Map field types to human readable names
    types = {
        1: "TEXT",
        2: "CHECKBOX",
        3: "RADIO",
        4: "LISTBOX",
        5: "COMBOBOX",
        6: "PUSHBUTTON",
        7: "TEXT_MULTILINE"
    }
    return types.get(field_type, f"UNKNOWN({field_type})")

def extract_pdf_data(pdf_path):
    print(f"Attempting to open PDF at: {os.path.abspath(pdf_path)}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File does not exist at {pdf_path}")
        return
        
    # Open the PDF
    doc = fitz.open(pdf_path)
    print(f"Successfully opened PDF")
    print(f"Number of Pages: {doc.page_count}")
    
    # Extract data from each page
    for page_num in range(doc.page_count):
        page = doc[page_num]
        print(f"\nPage {page_num + 1}:")
        print("=" * 80)
        
        # Extract all text blocks with their positions
        print("\nText Content:")
        print("=" * 80)
        blocks = page.get_text("dict")["blocks"]
        for i, block in enumerate(blocks, 1):
            if block.get("type") == 0:  # Type 0 means text
                print(f"\nText Block #{i}:")
                print("-" * 40)
                
                # Get the block's bounding box
                bbox = block["bbox"]
                print(f"Position: (x1={bbox[0]:.2f}, y1={bbox[1]:.2f}, x2={bbox[2]:.2f}, y2={bbox[3]:.2f})")
                
                # Print each line in the block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:  # Only print non-empty text
                            font = span["font"]
                            size = span["size"]
                            color = span["color"]
                            print(f"Text: {text}")
                            print(f"Font: {font}, Size: {size:.1f}, Color: {color}")
                            print(f"Span Position: (x1={span['bbox'][0]:.2f}, y1={span['bbox'][1]:.2f}, x2={span['bbox'][2]:.2f}, y2={span['bbox'][3]:.2f})")
                            print("-" * 20)
        
        # Get form fields
        fields = page.widgets()
        if fields:
            print("\nForm Fields Details:")
            print("=" * 80)
            for i, field in enumerate(fields, 1):
                print(f"\nField #{i}:")
                print("-" * 40)
                
                # Basic field information
                print(f"Field Name: {field.field_name}")
                print(f"Field Type: {get_field_type_name(field.field_type)} ({field.field_type})")
                print(f"Field Value: {field.field_value}")
                
                # Field rectangle (coordinates)
                rect = field.rect
                print(f"\nPosition and Size:")
                print(f"- Coordinates (x1, y1, x2, y2): ({rect.x0:.2f}, {rect.y0:.2f}, {rect.x1:.2f}, {rect.y1:.2f})")
                print(f"- Width x Height: {rect.width:.2f} x {rect.height:.2f}")
                
                # Field flags and properties
                print("\nField Properties:")
                print(f"- Field Flags: {field.field_flags}")
                
                # Get text format (if available)
                try:
                    text_format = field.text_format
                    if text_format:
                        print("\nText Format:")
                        for key, value in text_format.items():
                            print(f"- {key}: {value}")
                except:
                    pass
                
                # Get field appearance (if available)
                try:
                    appearance = field.appearance
                    if appearance:
                        print("\nAppearance:")
                        for key, value in appearance.items():
                            print(f"- {key}: {value}")
                except:
                    pass
                
                # Get border style (if available)
                try:
                    border_style = field.border_style
                    if border_style:
                        print("\nBorder Style:")
                        for key, value in border_style.items():
                            print(f"- {key}: {value}")
                except:
                    pass
        
        # Get annotations
        annots = page.annots()
        if annots:
            print("\nAnnotations Details:")
            print("=" * 80)
            for i, annot in enumerate(annots, 1):
                print(f"\nAnnotation #{i}:")
                print("-" * 40)
                print(f"Type: {annot.type}")
                print(f"Content: {annot.info.get('content', 'N/A')}")
                
                # Get annotation rectangle
                rect = annot.rect
                print(f"\nPosition:")
                print(f"- Coordinates (x1, y1, x2, y2): ({rect.x0:.2f}, {rect.y0:.2f}, {rect.x1:.2f}, {rect.y1:.2f})")
                
                # Print all annotation info
                print("\nAnnotation Properties:")
                for key, value in annot.info.items():
                    if key != 'content':  # Skip content as we already printed it
                        print(f"- {key}: {value}")
    
    doc.close()

if __name__ == "__main__":
    pdf_path = "empty-photo-pdf.pdf"
    try:
        extract_pdf_data(pdf_path)
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc() 