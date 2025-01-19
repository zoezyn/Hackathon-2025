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

from typing import List, Dict
import os
from dotenv import load_dotenv

from pdfagent.load_template import load_template
from thought_logging import push_to_logging

load_dotenv()


auth_client_secret = AuthApiKey()

document_store = WeaviateDocumentStore(url="https://fvcvazeztmaddxm0xv9dgg.c0.europe-west3.gcp.weaviate.cloud",
                                       auth_client_secret=auth_client_secret)


def noneifempty(s):
    if s == "":
        return None
    return s


def store_data(data: List[Dict[str, str]]):
    index_to_weaviate = Pipeline()

    index_to_weaviate.add_component("splitter", DocumentSplitter())
    index_to_weaviate.add_component("embedder", OpenAIDocumentEmbedder())
    index_to_weaviate.add_component("writer", DocumentWriter(document_store))
    index_to_weaviate.connect("splitter", "embedder")
    index_to_weaviate.connect("embedder", "writer")
    index_to_weaviate.run({"documents": [Document(content=c['data'], id=noneifempty(c.get('id'))) for c in data]})
    push_to_logging(f"Data stored successfully: {len(data)} docs", "RAG")


def make_context_prompt(query):
    referenced_rag = Pipeline()
    referenced_rag.add_component("query_embedder", OpenAITextEmbedder())
    referenced_rag.add_component("retriever", WeaviateEmbeddingRetriever(document_store=document_store))
    referenced_rag.add_component("prompt", ChatPromptBuilder(variables=["documents"]))
    # referenced_rag.add_component("llm", OpenAIChatGenerator(model="gpt-4o-2024-11-20"))

    referenced_rag.connect("query_embedder.embedding", "retriever.query_embedding")
    referenced_rag.connect("retriever.documents", "prompt.documents")

    message_template = load_template("rag_docs.ninja")

    messages =[ChatMessage.from_user(message_template)]

    result = referenced_rag.run({"query_embedder": {"text": query},
                                "retriever": {"top_k": 5},
                                "prompt": {"template_variables": {"query": query}, "template": messages}})

    return result['prompt']['prompt'][0].text
