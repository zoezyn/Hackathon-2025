import os
from typing import List, Dict
import fitz



def get_field_type_name(field_type: int) -> str:
    """Map field types to human readable names."""
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


def extract_pdf_fields(pdf_path: str) -> List[Dict]:
    """
    Extract form fields from a PDF file using PyMuPDF.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[Dict]: List of fields with their properties
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    # Open the PDF
    doc = fitz.open(pdf_path)
    fields = []
    
    # Extract fields from each page
    for page_num in range(doc.page_count):
        page = doc[page_num]


        
        # Get form fields (widgets) from the page
        for field in page.widgets():
            if field.field_type == 2:
                # FIXME: filter checkboxes for now
                continue

            field_data = {
                "name": field.field_name,
                "type": {
                    "id": field.field_type,
                    "name": get_field_type_name(field.field_type)
                },
                "value": field.field_value,
                "page": page_num + 1,
                "position": {
                    "x1": field.rect.x0,
                    "y1": field.rect.y0,
                    "x2": field.rect.x1,
                    "y2": field.rect.y1,
                    "width": field.rect.width,
                    "height": field.rect.height
                },
                "flags": field.field_flags,
                "is_required": bool(field.field_flags & 2)  # Check if field is required
            }
            fields.append(field_data)
    
    doc.close()
    return fields


def _find_answer(label: str, page:int, data: dict) -> str|None:
    print(data, label, page)
    for field in data.get("fields", []):
        print('--------->', field)
        if field.get("name") == label:
            return field.get("answer")
    return None


def fill_pdf(pdf_path: str, data: dict) -> fitz.Document:
    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]

        for field in page.widgets():
            answer = _find_answer(field.field_name, page_num, data)
            print("ANSWER FOR: ", field.field_name, "is: ", answer)
            if answer is not None:
                field.field_value = answer
                print("Field filled: ", field.field_name, "with value: ", answer)
                field.update()

    return doc

        

