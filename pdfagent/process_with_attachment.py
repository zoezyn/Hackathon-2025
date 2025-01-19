import json

from haystack_integrations.document_stores.weaviate import WeaviateDocumentStore, AuthApiKey
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack import Document, Pipeline
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.retrievers.weaviate import WeaviateEmbeddingRetriever

from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.builders import ChatPromptBuilder

from functions import fill_responses_to_pdf
from pdfagent.chat_with_tools import chatbot_with_tools
from pdfagent.load_template import load_template
from pdfagent.rag import make_context_prompt
from pdfagent.tools.email_qa import request_information_emails_function
from thought_logging import push_to_logging


def extract_json(e: str):
    from_i = e.index("STARTJSON")
    to_i = e.index("ENDJSON")
    print(e[from_i+1 + 8:to_i])
    return json.loads(e[from_i+1 + 8:to_i])


_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_emails_func",
            "description": f"This a tool useful to send emails to colleagues. You can send multiple emails at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emails": {
                        "type": "array",
                        "description": "The emails to send. Each email should have a subject and a body",
                        "items": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string"},
                                "subject": {"type": "string"},
                                "body": {"type": "string"},
                            },
                        }
                    }
                },
                "required": ["question"],
            },
        },
    }
]


_AVAILABLE_FUNCTIONS = {
    "send_emails_func": request_information_emails_function
}


def process_with_attachment(email, attachment_data):
    rag_query = f"""
    Get a list of all colleagues and their emails
    
    You need to answer the following questions:
    {"\n".join([f"{q['name']}" for q in attachment_data['questions']])}
    """
    rag_prompt = make_context_prompt(rag_query)
    user_prompt = load_template(
        "with_pdf.ninja"
    ).replace(
        "{{questions_json}}",
        json.dumps(attachment_data['questions'])
    ).replace("{{context}}", email['body'])
    chat_messages = [
        ChatMessage.from_system(load_template("with_pdf_system.ninja")),
        ChatMessage.from_user(rag_prompt),
        ChatMessage.from_user(user_prompt)
    ]

    push_to_logging(f"Chat messages: {chat_messages}", "AI")

    print(chat_messages)

    response = chatbot_with_tools(chat_messages, _AVAILABLE_FUNCTIONS, _TOOLS)

    structured = extract_json(response)

    res_path = fill_responses_to_pdf(attachment_data['path'], {'questions': structured})

    return {
        'body': response,
        'attachments': [res_path]
    }
