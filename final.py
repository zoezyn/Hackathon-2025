from haystack.utils import Secret
from haystack_integrations.components.generators.mistral import MistralChatGenerator
from markitdown import MarkItDown
import fitz  # PyMuPDF
import os
from typing import Dict, List, Tuple
from haystack import Pipeline
from haystack.dataclasses import ChatMessage
from pathlib import Path
import json



def convert_pdf_to_markdown(pdf_path: str, output_path: str = None) -> str:
    """
    Convert a PDF file to Markdown.
    
    Args:
        pdf_path (str): Path to the input PDF file
        output_path (str, optional): Path where to save the markdown output
        
    Returns:
        str: The markdown content
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("Input file must be a PDF")

    try:
        # Initialize MarkItDown and convert PDF
        md = MarkItDown()
        result = md.convert(pdf_path)
        markdown_content = result.text_content
        
        # Save markdown if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return markdown_content

    except Exception as e:
        raise Exception(f"Error converting PDF to markdown: {str(e)}")

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
    
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        fields = []
        
        # Extract fields from each page
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Get form fields (widgets) from the page
            for field in page.widgets():
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

    except Exception as e:
        raise Exception(f"Error extracting PDF fields: {str(e)}")

def process_pdf_document(pdf_path: str) -> Tuple[str, List[Dict], List[Dict]]:
    """
    Process a PDF document using Haystack 2.0
    """
    try:
        # Convert to markdown
        markdown_content = convert_pdf_to_markdown(pdf_path, "output.md")
        
        # Extract fields
        fields = extract_pdf_fields(pdf_path)
        
        # Initialize Mistral Generator
        generator = MistralChatGenerator(
            api_key=Secret.from_token(" w9FjkpxYzDypCXLnGSg4JY64xxz2XYOQ"),
            model="mistral-large-latest"
        )
        
        # Create pipeline
        pipeline = Pipeline()
        pipeline.add_component("llm", generator)
        
        # Get sections using Mistral
        section_prompt = ChatMessage.from_user(
            f"""Analyze the following markdown content and split it into main sections, maintaining the exact order.
            Create a JSON array where each object has a 'title' and 'content' field.
            Content: {markdown_content}"""
        )
        
        result = pipeline.run({
            "llm": {
                "messages": [section_prompt]
            }
        })
        
        sections = json.loads(result["llm"]["replies"][0])
        
        # Match fields to sections
        matched_fields = []
        for field in fields:
            field_info = field.copy()
            field_info['sections'] = []
            
            for section in sections:
                field_prompt = ChatMessage.from_user(
                    f"""Does this field belong to this section? Answer only with 'yes' or 'no'.
                    Section: {section['title']}
                    Field name: {field['name']}
                    Field type: {field['type']['name']}
                    Page: {field['page']}"""
                )
                
                result = pipeline.run({
                    "llm": {
                        "messages": [field_prompt]
                    }
                })
                
                if result["llm"]["replies"][0].lower().strip() == 'yes':
                    field_info['sections'].append(section['title'])
            
            matched_fields.append(field_info)
        
        return markdown_content, sections, matched_fields

    except Exception as e:
        raise Exception(f"Error processing PDF document: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        pdf_path = "empty-pdf.pdf"  # Replace with your PDF path
        
        # Process the PDF
        markdown, sections, matched_fields = process_pdf_document(pdf_path)
        
        # Print results
        print("\nDocument Sections:")
        for i, section in enumerate(sections, 1):
            print(f"\n{i}. {section['title']}")
            print("-" * 50)
            print(section['content'][:200] + "...")  # Print first 200 chars
        
        print("\nFields with their sections:")
        for field in matched_fields:
            print(f"\nField: {field['name']}")
            print(f"Type: {field['type']['name']}")
            print(f"Found in sections: {', '.join(field['sections'])}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
