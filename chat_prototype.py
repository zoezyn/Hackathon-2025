import gradio as gr
import os
import json
from typing import List, Dict
import dotenv
dotenv.load_dotenv()

from haystack_integrations.components.generators.mistral import MistralChatGenerator


from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator

chat_generator = OpenAIChatGenerator(model="gpt-4o-2024-11-20")
# chat_generator = MistralChatGenerator(model="mistral-large-latest")


response = None

colleagues = {
    'Johanna': {
        'email': 'johanna@corporate.com',
        'responsibilities': 'HR, Procuremeent, Invoicing, General Admin'
    },
    'Ellie': {
        'email': 'ellie@corporate.com',
        'responsibilities': 'Sales, Marketing'
    },
    'John': {
        'email': 'john@corporate.com',
        'responsibilities': 'Cleaning, Security'
    }
}


company_info = open("company_info.txt", "r").read()


messages = [
    ChatMessage.from_system(
        f"""You are a helpful and knowledgeable agent who replies to questions from the user.
        You can use the 'send_emails_func' tool to send emails to colleagues and ask for more information if you need to.
        Before telling a user that you don't have the information they are asking for, you should try to find it in the list of colleagues.
        Here is a list of the colleagues you can send emails to:
        {json.dumps(colleagues)}
        """
    ),
    ChatMessage.from_system(
        f"""Here is the company information:
        {company_info}
        """
    )
]


tools = [
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

dumb_replies = {
    'johanna@corporate.com': 'The VAT number of the company is 1234567890',
    'ellie@corporate.com': 'Our main product is a software called "The Hub"',
    'john@corporate.com': 'No dogs are allowed in the office'
}


def send_emails_function(emails: List[Dict[str, str]]):
    replies = ""
    for email in emails:
        print(f"Sending email to {email['email']}: {email}")
        # replies[email['email']] = dumb_replies[email['email']]
        replies += f"reply to email to {email['email']} with subject {email['subject']}: {dumb_replies[email['email']]}\n\n"
    return replies


available_functions = {
    "send_emails_func": send_emails_function
}


def chatbot_with_fc(message, history):
    print("-------------------------")
    print("MESSAGE", message)
    global available_functions
    global tools
    messages.append(ChatMessage.from_user(message))
    response = chat_generator.run(messages=messages, generation_kwargs={"tools": tools})

    print("CHAAAAAAAAAAAAAT", ", ".join([str(m) for m in messages]))

    while True:
        # if OpenAI response is a tool call
        if response and response["replies"][0].meta["finish_reason"] == "tool_calls":
            tool_call = response["replies"][0].tool_call

            ## Find the correspoding function and call it with the given arguments
            function_to_call = available_functions[tool_call.tool_name]
            function_response = function_to_call(**tool_call.arguments)
            ## Append function response to the messages list using `ChatMessage.from_function`
            messages.append(ChatMessage.from_assistant(tool_calls=[tool_call]))
            messages.append(
                ChatMessage.from_tool(
                    origin=tool_call,
                    tool_result=function_response,
                )
            )
            response = chat_generator.run(messages=messages, generation_kwargs={"tools": tools})
            print("->> ", tool_call.tool_name, tool_call.arguments, " ->> ", function_response)
            print("FUNCTION RESPONSE", response)
        else:
            print("NO TOOL CALL, finishing", response)
            messages.append(response["replies"][0])
            break
    return response["replies"][0].text


# gr.ChatInterface(
#     fn=chatbot_with_fc, 
#     type="messages"
# ).launch()

# print(chat_generator.run(messages=[ChatMessage.from_user("What is the VAT number of the company?")], generation_kwargs={"tools": tools}))


questions = [
    {'id': '1', 'question': "What is the VAT number of the company?"},
    {'id': '2', 'question': "What is the email address of the company?"},
    {'id': '3', 'question': "What is the telephone number of the company?"},
    {'id': '4', 'question': "What is the address of the company?"},
]


print(
    chatbot_with_fc(
        f"""What follows is a list of questions. Evaluate each question and say if you
          know the answer or not. If not, ask colleagues for the information you need.
          
          Upon receiving the answer, reply with JSON of questions in format {json.dumps({"id": "QUESTION_ID", "answer": "REPLY"})}
          
          {json.dumps(questions)}""", []))