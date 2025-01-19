from uuid import uuid3, UUID, uuid4
import json
import logging
from pdf_handler import extract_pdf_fields, fill_pdf


import json5

from mistralai import Mistral
import base64
import os



ns = uuid3(UUID("ea3a8f48-d645-11ef-9213-5bb92fa5c704"), "fields")


def questions_from_pdf(file_path: str) -> dict:
    #fields = extract_pdf_fields(file_path)
    fields = enhance_form_data(file_path).get("fields", [])
    res = {"questions": []}

    for field in fields:
        my_id = _field_to_id(field)
        res["questions"].append({
            "id": my_id,
            "name": field.get("name"),
            "question": field.get("question")
        })
    return res


def _fields_per_page(file_path: str) -> dict:
    fields = extract_pdf_fields(file_path)
    res = {"pages": {}}
    for field in fields:
        page = field.get("page")
        if page not in res["pages"].keys():
            page_data = {
                "page_number": page,
                "fields": []
            }
            res["pages"].update({page: page_data})
        page_data["fields"].append({
            "name": field.get("name"),
            "label": field.get("label"),
            "type": field.get("type"),
            "position": field.get("position"),
            "flags": field.get("flags"),
            "is_required": field.get("is_required")
        })
    return res


def fill_responses_to_pdf(pdf_path: str, responses: dict) -> str:
    """
    sample responses:
    {
  "questions": [
    {
      "id": "86627cac-7a84-3a20-b42d-cec61c36b6e6",
      "name": "Company",
      "response": "acme inc"
    },
    {
      "id": "0ae69915-2b2e-3c87-b468-663e1b023dfa",
      "name": "DHL EXPRESS account number optional",
      "response": "acc no"
    },

    """


    fields = extract_pdf_fields(pdf_path=pdf_path)
    for response in responses.get("questions", []):
        field_id = response.get("id")
        for field in fields:
            parsed_field_id = _field_to_id(field)
            if field_id == parsed_field_id:
                field["answer"] = response.get("response")
    doc = fill_pdf(pdf_path, {"fields": fields})
    out_path = f"/tmp/filled_{uuid4()}.pdf"
    logging.info(f"filled PDF saved at: {out_path}")
    doc.save(out_path)
    doc.close()
    return out_path

def _field_to_id(field: dict) -> str:
    data = {
        "name": field.get("name"),
        "page": field.get("page"),
    }
    return str(uuid3(ns, json.dumps(data)))



def _page_fields_to_prompt(fields: list[dict]):
    field_names = [field.get("name") for field in fields]
    return ", ".join(field_names)


def enhance_form_data(input_file_path: str):
        # Specify model
    model = "pixtral-12b-2409"
    token = os.environ.get("MISTRAL_TOKEN")

    ppf = _fields_per_page(input_file_path)

    res_with_questions = {"fields": []}

    # Initialize the Mistral client
    client = Mistral(api_key=token)

    pages_images = _to_images(input_file_path)

    page = 1

    for page_image in pages_images:


        if page not in ppf["pages"]:
            continue

        page_fields = ppf["pages"][page]["fields"]
        prompt_fields = _page_fields_to_prompt(page_fields)

        img = open(page_image.get("image"), "rb").read()
        base_img = base64.b64encode(img).decode("utf-8")

        # Define the messages for the chat
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
    you are an expert in understanding forms. I have the form attatched, and I do know there are fields named {prompt_fields}. 
    
    please formulate a question for each field. only output a valid json, with the key field name, value question for the field


    """
                    },
                                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base_img}" 
                }
                ]
            }
        ]

        # Get the chat response
        chat_response = client.chat.complete(
            model=model,
            messages=messages
            
        )

        read_response = chat_response.choices[0]

        cnt = read_response.message.content

        cnt = cnt.strip("```")
        if cnt.startswith("json"):
            cnt = cnt[4:]

        cnt = cnt.strip("```")

        res_data = json5.loads(cnt)

        for key, val in res_data.items():
            for field in page_fields:
                if field.get("name") == key:
                    field.update({"question": val})
                    res_with_questions["fields"].append(field)

        page = page + 1

    return res_with_questions


def _to_images(input_file_path: str) -> list: 
    from pdf2image import convert_from_path
    images = convert_from_path(input_file_path)
    page = 0
    res = []
    for image in images:
        image.save(f"/tmp/out_{page}.png", "PNG")
        page =  page  + 1
        res.append({
            "page": page,
            "image": f"/tmp/out_{page}.png"}
        )
    return res
