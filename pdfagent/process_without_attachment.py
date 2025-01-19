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

from pdfagent.chat_with_tools import chatbot_with_tools
from pdfagent.load_template import load_template
from pdfagent.rag import make_context_prompt, store_data
from pdfagent.tools.email_qa import request_information_emails_function

messages = [
    ChatMessage.from_system(
        f"""You are a helpful and knowledgeable agent who replies to questions from the user.
        Your colleagues will tell you the data you need to store.
        You can use the 'store_data_func' tool to store data in a database.
        If the user asks for information that you already have, don't update anything and instead provide the information
        """
    )
]


_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "store_data_func",
            "description": f"This a tool useful to store data in a database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "The data to store. If overwriting, provide the id of the data to overwrite. If not, keep id empty",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "data": {"type": "string"},
                            },
                        }
                    }
                },
                "required": ["question"],
            },
        },
    }
]

def store_data_function(data):
    print(f"Storing data: {data}")
    store_data(data)
    return "Data stored successfully"


_AVAILABLE_FUNCTIONS = {
    "store_data_func": store_data_function
}


def process_without_attachment(email):
    system_prompt = f"""
You are a helpful and knowledgeable agent who replies to questions from the user.
Your colleagues will tell you the data you need to store.
You can use the 'store_data_func' tool to store data in a database.
If the user asks for information that you already have, don't update anything and instead provide the information
"""
    email_prompt = f"""
**{email['subject']}**

{email['body']}
"""
    rag_prompt = make_context_prompt(email_prompt)
    chat_messages = [
        ChatMessage.from_system(system_prompt),
        ChatMessage.from_user(rag_prompt),
        ChatMessage.from_user(email_prompt)
    ]

    response = chatbot_with_tools(chat_messages, _AVAILABLE_FUNCTIONS, _TOOLS)

    return {
        'body': response,
        'attachments': []
    }
