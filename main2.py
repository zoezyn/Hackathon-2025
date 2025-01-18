from PyPDF2 import PdfReader

pdf_path = "customssave.pdf"
reader = PdfReader(pdf_path)

print(f"Number of Pages: {len(reader.pages)}")
print(f"Is Encrypted: {reader.is_encrypted}")
print("\nOriginal PDF Fields:")
print("-" * 50)

field_text = reader.get_form_text_fields()
print("")
