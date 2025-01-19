from thought_logging import push_to_logging
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator


def chatbot_with_tools(messages, available_functions, tools):
    print(messages)
    chat_generator = OpenAIChatGenerator(model="gpt-4o-2024-11-20")
    response = chat_generator.run(messages=messages, generation_kwargs={"tools": tools})

    while True:
        if response and response["replies"][0].meta["finish_reason"] == "tool_calls":
            tool_call = response["replies"][0].tool_call

            push_to_logging(f"Tool call: {tool_call.tool_name} with arguments: {str(tool_call.arguments)[:100]}", "AI: tool call")

            function_to_call = available_functions[tool_call.tool_name]
            function_response = str(function_to_call(**tool_call.arguments))

            push_to_logging(f"Function response: {function_response}", "AI: function response")

            messages.append(ChatMessage.from_user(function_response))
            # messages.append(
            #     ChatMessage.from_tool(
            #         origin=tool_call,
            #         tool_result=function_response,
            #     )
            # )

            response = chat_generator.run(messages=messages, generation_kwargs={"tools": tools})
            push_to_logging(f"New response: {response}", "AI: new response")
        else:
            messages.append(response["replies"][0])
            break
    return response["replies"][0].text
