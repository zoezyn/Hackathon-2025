from PyPDF2 import PdfReader, PdfWriter

def print_field_details(field_name, field_data):
    print(f"Field Name: {field_name}")
    print(f"Type: {field_data.get('/FT', 'Not specified')}")
    print(f"Value: {field_data.get('/V', 'Empty')}")
    print(f"Default Value: {field_data.get('/DV', 'Not specified')}")
    print(f"Alternate Name: {field_data.get('/TU', 'Not specified')}")
    print(f"Flags: {field_data.get('/Ff', 'None')}")
    print(f"Max Length: {field_data.get('/MaxLen', 'Not specified')}")
    
    # Try to get the widget annotation for position info
    if '/Kids' in field_data:
        for kid in field_data['/Kids']:
            if hasattr(kid, 'get_object'):
                widget = kid.get_object()
                if '/Rect' in widget:
                    rect = widget['/Rect']
                    print(f"Position (x1,y1,x2,y2): {rect}")
                    print(f"Width: {rect[2] - rect[0]}")
                    print(f"Height: {rect[3] - rect[1]}")
    elif '/Rect' in field_data:
        rect = field_data['/Rect']
        print(f"Position (x1,y1,x2,y2): {rect}")
        print(f"Width: {rect[2] - rect[0]}")
        print(f"Height: {rect[3] - rect[1]}")
    
    # Additional properties
    if '/Q' in field_data:
        alignment = {0: 'Left', 1: 'Center', 2: 'Right'}
        print(f"Text Alignment: {alignment.get(field_data['/Q'], 'Unknown')}")
    
    print("-" * 50)

# First, list all fields in the original PDF
pdf_path = "customssave.pdf"
reader = PdfReader(pdf_path)

print(f"Number of Pages: {len(reader.pages)}")
print(f"Is Encrypted: {reader.is_encrypted}")
print("\nOriginal PDF Fields:")
print("-" * 50)

all_fields = reader.get_fields()
for field_name, field_data in all_fields.items():
    print_field_details(field_name, field_data)

# Now create a new PDF with filled EORI field
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

# Update form field
writer.update_page_form_field_values(
    writer.pages[0], 
    {"Economic Operators Registration and Identification number": "Hello World"}
)

# Save the modified PDF
output_pdf = "customssave_filled.pdf"
with open(output_pdf, "wb") as output_file:
    writer.write(output_file)

print(f"\nPDF saved as {output_pdf}")

# Read and display fields from the new PDF to verify
print("\nNew PDF Fields:")
print("-" * 50)
new_reader = PdfReader(output_pdf)
new_fields = new_reader.get_fields()
new_reader.get_form_text_fields()
for field_name, field_data in new_fields.items():
    print_field_details(field_name, field_data)

