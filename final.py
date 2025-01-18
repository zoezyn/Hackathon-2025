from time import sleep

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
from haystack.components.generators.utils import print_streaming_chunk

cached = [
  {
    "title": "Contact Information",
    "content": "Please return the documents to:\nDHL Hub Leipzig GmbH, Customer Database Coordinator, Postfach 11 11, 04435 Schkeuditz\nE-Mail: lejhubcdb@dhl.com\n\nTelefax: +49 (0) 341 / 4499 88 6104\n\nDo you have any questions?\nGive us a call.\nTelephone: +49 (0) 341 / 4499 4480",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "Company Information",
    "content": "Company\n\nStreet, No.\n\nTelephone\n\nE-Mail\n\nDHL EXPRESS account number (optional)\n\nCDB-reference (optional)\n\nZIP, City\n\nFax\n\nContact",
    "is_there_fields_to_fill_in": True,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "EORI and Branch Number",
    "content": "EORI-NUMBER\nEconomic Operators´ Registration and Identification number\n\nBRANCH NUMBER\n\n» A branch number is only to be indicated if this has been assigned by the master data management of the Customs Authorities to a non-legal part of the company (branch or commercial unit). If you have a branch number, please send us the confirmation letter of the Customs Authorities. Further information regarding the EORI number can be found under zoll.de.",
    "is_there_fields_to_fill_in": True,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "Customs Clearance Agreement",
    "content": "DHL Express Germany GmbH and the importer agree the customs clearance for incoming import shipments until revoked in writing. For this purpose, the importer grants DHL Express a power of attorney for direct customs representation in the name and for the account of the importer for the customs declaration with the specified EORI number. This authorization also entitles to grant a sub-authorization. The sub-authorization entitles to act as a customs representative and to grant a further sub-authorization. Customs clearance is performed by DHL Express itself or DHL Hub Leipzig GmbH or DHL Airways GmbH as customs service providers and sub-authorized representatives of DHL Express. DHL Express and its customs service providers are entitled to further subcontract and sub-authorized third parties. Annex I for the settlement of import duties and customs services is an integral part of this order.\n\nIf available, the importer shall provide DHL Express with a goods tariff list (incl. eleven-digit goods tariff number) as well as any permits required for clearance or valid binding information (e.g. binding customs tariff information). The importer is aware that incorrect or missing information and documents for the customs declaration may lead to a different assessment or subsequent levying of import duties for which he is responsible. The importer therefore assures that he has provided all information and documents completely and correctly.\n\nThe authorized direct representation in accordance with Article 19 of the Union Customs Code also includes the application for post-clearance recovery, reimbursement or remission in the case of customs declarations to be amended or the invalidation of the customs declaration. The importer is aware that the actions of DHL Express or its customs service providers and sub-agents as its direct representative have direct legal effect against it.",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "VAT Deduction Eligibility",
    "content": "We are eligible for deduction of prior VAT:\n\nYES\n\nNO\n\nVAT-ID:\n\n» A company is entitled to prior VAT who are not subject to the small business operator regulations (§19 UStG) and raises VAT to its revenues.",
    "is_there_fields_to_fill_in": True,
    "is_there_any_checkbox_to_check": True,
    "count_of_checkbox": 2
  },
  {
    "title": "Signature and Stamp",
    "content": "Name (in capital letters)\n\nValid customer signature\n\nCity, date\n\nCompany stamp",
    "is_there_fields_to_fill_in": True,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "Billing of Import Duties and Taxes",
    "content": "Please return the documents to:\nDHL Hub Leipzig GmbH, Customer Database Coordinator, Postfach 11 11, 04435 Schkeuditz\nE-Mail: lejhubcdb@dhl.com\n\nTelefax: +49 (0) 341 / 4499 88 6104\n\nDo you have any questions?\nGive us a call.\nTelephone: +49 (0) 341 / 4499 4480\n\nCompany\n\nStreet, No.\n\nDHL EXPRESS account number (optional)\n\nCDB-reference (optional)\n\nZIP, City",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "Deferment Account",
    "content": "   USING A OWN DEFERMENT ACCOUNT\nCustoms duties and taxes are debited directly via the customer's own customs deferment account. The fixed import duties are not due until the 16th of the following month and are collected directly by the customs payment office. The customer provides the necessary information using the additional \"Deferment account\" form (> download). Billing of used customs services and expenses may be only invoiced on invoice.\n\n»  Note: For more information on how to apply a deferment account, please visit www.zoll.de",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": True,
    "count_of_checkbox": 1
  },
  {
    "title": "Options for Payment on Invoice",
    "content": "   A.   Issue a direct debit authorisation via a valid SEPA mandate for your DHL Express account number\n\nWhen issuing a SEPA mandate, you will receive a 50 % discount on the costs incurred for using DHL's own deferment account. The additional fee is therefore only 1 % of the import duties paid, but at least EUR 6.25 plus VAT per item handled (Service Duty Tax Processing). DHL Express Germany GmbH is, however, not obliged to utilise its own deferment accounts and may refuse customs clearance of shipments in individual cases and for valid reasons at its own discretion. The invoiced amounts are due for payment within 7 days, unless otherwise agreed in writing.\n\n» Note: Just use our DHL Express authorization form (> download).\n\n   Not required, DHL Express has already a valid SEPA mandate.\n\n    B.   Transfer of customs duties and taxes disbursed by DHL Express Germany GmbH\n\nIn the case of bank transfer, the additional fee for the use of DHL's own deferment account is charged as standard in the amount of 2 % of the disbursed import duties, but at least €12.50 plus VAT, per shipment handled (Service Duty Tax Processing). Invoiced amounts are due for payment within 7 days, unless otherwise agreed in writing.\n\nStorage as a result of delays attributable to the customer is subject to a storage fee of EUR 11 per shipment and per day + EUR 0.22 per kg/day plus VAT from the 3rd day. Customs clearance is included for up to 5 items subject to-goods tariffs. Starting with the 6th item subject to a goods tariff, there will be a charge of EUR 5.00 plus VAT per item. Paper-based customs clearance (luggage or shipment for private purposes) is charged at EUR 45.00 and returned goods at EUR 40.00 plus VAT per shipment. In the case of multilingualism, the German version is legally binding. This Agreement shall be governed by German law. The court of jurisdiction is Bonn.",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 3
  },
  {
    "title": "Company Information",
    "content": "DHL Express Germany GmbH\nManagement:\n\nRegistergericht Bonn, HRB 13192\nMustafa Tonguc (Chairman), Kris Van Humbeek\n\nChairman of Supervisory Board:\n\nSabine Müller\n\nDHL Hub Leipzig GmbH and DHL Express Germany GmbH are approved as Authorized Economic Operator: AEO C/S 100593",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  },
  {
    "title": "Notes on Customs Clearance",
    "content": "NOTES ON CUSTOMS CLEARANCE OF YOUR IMPORT SHIPMENTS\n\nIn order to avoid delays in the customs clearance of your import shipments, we ask you to observe the following advices.\n\nEORI number\n(Economic Operators´ Registration and Identification Number – Number to identify economic operators)\nCustoms clearance without a valid EORI number is not possible. Therefore we need your EORI number for the customs clearance of your shipments. This number must be registered with a legal entity permanently resident in the EU. Information on the EORI number can be found on the official website of German customs www.zoll.de/EN/\n\nCustoms clearance order\n(Power of attorney to handle your import shipments)\nIn order to be able to clear shipments quickly and permanently for free circulation, we ask you to issue a general customs clearance order. This is valid until revoked and authorizes DHL HUB Leipzig to register your import shipments on your behalf and for your account (direct representation) without prior time-consuming contact. Further information on general customs clearance via DHL Express is available on our website at www.dhl.com/en/express/customs_support.html\n\nCommercial-/ Pro forma invoice\n(Shipment accompanying paperwork as a basis for the customs declaration of your shipment in the import country)\nUnder-valuated shipments repeatedly lead to delays in customs clearance. Point out to your supplier the correct value of the goods, i.e. the amounts you actually pay to your supplier (in the case of a commercial invoice) or the realistic market value (in the case of a pro forma invoice). At the most during a customs inspection, unpleasant questions from the customs authorities can arise if the value of the goods is incorrect. If the shipment recipient is different from the importer, a distinction must be made between the shipment recipient (SHIP-TO) and invoice recipient (BILL-TO) on the commercial or pro forma invoice. This simplifies the correct assignment of the shipment to a customs clearance order. In addition to an exact description of the goods (e.g. condition, material, intended use), it is also essential to state a goods tariff number (HS code, at least 6 digits) and to indicate the transport costs and possible surcharges (e.g. transport insurance) for a correct declaration of your shipment. Please also make sure that you specify an Incoterm correctly. If this is not available, we must declare the goods with EXW (ex works).\n\nCommodity tariff list\n(Classification of your goods and assignment of the correct goods tariff number)\nDo you have a goods tariff list (article number & article description versus goods tariff number)? Then send it to us for the correct tariff classification of your goods: lejhubcdb@dhl.com. Please let us know whether we can rate the goods to be imported ourselves to the best of our knowledge and belief or whether we should notify you in this case for clearance authorization with costs.\n\nDO YOU HAVE QUESTIONS REGARDING YOUR IMPORT INSTRUCTIONS?\n\nThen please send an e-mail to lejhubcdb@dhl.com\n\nDHLE\n\nExpressGermanyGmbH,\n\nMarketingServices,\n\nas of01/2025",
    "is_there_fields_to_fill_in": False,
    "is_there_any_checkbox_to_check": False,
    "count_of_checkbox": 0
  }
]


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

def process_pdf_document(pdf_path: str) -> list[dict[str, str]]:
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
            api_key=Secret.from_token("w9FjkpxYzDypCXLnGSg4JY64xxz2XYOQ"),
            model="mistral-large-latest",
            streaming_callback=print_streaming_chunk,
            generation_kwargs={"temperature": 0.0}
        )
        
        # Create pipeline
        pipeline = Pipeline()
        pipeline.add_component("llm", generator)
        
        # Get sections using Mistral
        section_prompt = ChatMessage.from_user(
            f"""Split this content into multiple logically grouped sections and return ONLY a JSON array where each object has a 'title', 'content', is_there_fields_to_fill_in, is_there_any_checkbox_to_check and count_of_checkbox field.
            For the is_the_any_checkbox_to_check field, answer only with true or false, depending on whether there are checkboxes to check in the section.
            If there are checkboxes to check, count the number of checkboxes and add that number to the count_of_checkbox field.
            For the is_there_fields_to_fill_in field, answer only with true or false, depending on whether there are fields to fill in the section.
            You should also group related information together based on:
            - Common themes or topics
            - Related form fields or data entries
            - Sequential or procedural steps that belong together
            - Contextually linked information
            - Preserve the markdown data and structure as much as possible
            
            Each section should be cohesive and self-contained, with clear thematic boundaries.
            Give your response as a json object without anything else.
            Content: {markdown_content}"""
        )
        
        #result = pipeline.run({
        #    "llm": {
        #        "messages": [section_prompt]
        #    }
        #})

        #extracted = result["llm"]["replies"][0].text.split("```json")[1].split("```")[0].strip()
        #sections = json.loads(extracted)
        sections = cached
        
        # Match fields to sections
        matched_fields = []
        for field in fields:
            field_info = field.copy()
            field_info['sections'] = []
            
            for section in sections:
                sleep(5)
                if not section["is_there_fields_to_fill_in"]:
                    continue
                section["fields"] = section.get("fields", [])
                field_prompt = ChatMessage.from_user(
                    f"""Does this field belong to this section? 
                    Answer with the probability from 1 to 100 and don't include any other information.
                    Field: {json.dumps(field_info, indent=2)}
                    
                    Section title: {section["title"]}
                    Section content: {section["content"]}
                    """
                )
                
                result = pipeline.run({
                    "llm": {
                        "messages": [field_prompt]
                    }
                })
                
                if float(result["llm"]["replies"][0].text.lower().replace(".", "").strip()) >= 95:
                    section["fields"].append(field)
                    print(f"Field matched to section: {field['name']} -> {section['title']}")
                    break

        return sections

    except Exception as e:
        raise Exception(f"Error processing PDF document: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        pdf_path = "empty-pdf.pdf"  # Replace with your PDF path
        
        # Process the PDF
        sections = process_pdf_document(pdf_path)
        
        # Print results
        print(sections)

            
    except Exception as e:
        print(f"Error: {str(e)}")
