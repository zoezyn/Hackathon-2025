import fitz  # PyMuPDF
import os
import json

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
    
    # Initialize the JSON structure
    pdf_data = {
        "document_info": {},
        "pages": []
    }
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    pdf_data["document_info"] = {
        "page_count": doc.page_count,
        "file_path": os.path.abspath(pdf_path)
    }
    
    # Extract data from each page
    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_data = {
            "page_number": page_num + 1,
            "text_blocks": [],
            "form_fields": [],
            "annotations": []
        }
        
        # Extract all text blocks with their positions
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") == 0:  # Type 0 means text
                block_data = {
                    "bbox": {
                        "x1": block["bbox"][0],
                        "y1": block["bbox"][1],
                        "x2": block["bbox"][2],
                        "y2": block["bbox"][3]
                    },
                    "lines": []
                }
                
                # Process each line and span
                for line in block["lines"]:
                    line_data = []
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:  # Only include non-empty text
                            span_data = {
                                "text": text,
                                "font": span["font"],
                                "size": span["size"],
                                "color": span["color"],
                                "position": {
                                    "x1": span["bbox"][0],
                                    "y1": span["bbox"][1],
                                    "x2": span["bbox"][2],
                                    "y2": span["bbox"][3]
                                }
                            }
                            line_data.append(span_data)
                    if line_data:  # Only add lines that have content
                        block_data["lines"].append(line_data)
                
                if block_data["lines"]:  # Only add blocks that have content
                    page_data["text_blocks"].append(block_data)
        
        # Get form fields
        fields = page.widgets()
        for field in fields:
            field_data = {
                "name": field.field_name,
                "type": {
                    "id": field.field_type,
                    "name": get_field_type_name(field.field_type)
                },
                "value": field.field_value,
                "position": {
                    "x1": field.rect.x0,
                    "y1": field.rect.y0,
                    "x2": field.rect.x1,
                    "y2": field.rect.y1,
                    "width": field.rect.width,
                    "height": field.rect.height
                },
                "flags": field.field_flags
            }
            page_data["form_fields"].append(field_data)
        
        # Get annotations
        annots = page.annots()
        if annots:
            for annot in annots:
                annot_data = {
                    "type": annot.type,
                    "content": annot.info.get("content", ""),
                    "position": {
                        "x1": annot.rect.x0,
                        "y1": annot.rect.y0,
                        "x2": annot.rect.x1,
                        "y2": annot.rect.y1
                    },
                    "properties": {k: v for k, v in annot.info.items() if k != "content"}
                }
                page_data["annotations"].append(annot_data)
        
        pdf_data["pages"].append(page_data)
    
    doc.close()
    return pdf_data

if __name__ == "__main__":
    pdf_path = "customssave_filled.pdf"
    try:
        pdf_data = extract_pdf_data(pdf_path)
        # Save to JSON file with pretty printing
        output_file = "pdf_content.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(pdf_data, f, indent=2, ensure_ascii=False)
        print(f"\nJSON data has been saved to {output_file}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        import traceback
        traceback.print_exc() 