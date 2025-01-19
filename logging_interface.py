import json
import redis
import gradio as gr
from thought_logging import push_to_logging, stream_chat


import gradio as gr
import random
import time

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history: list):
        return "", history + [{"role": "user", "content": user_message}]

    def bot(history: list):
        history.append({"role": "assistant", "content": ""})
        print("HELLO", history)

        for message in stream_chat():
            print("GOT MESSAGE", message)
            if message["append"]:
                history[-1].content += "\n\n" + message["message"]
            else:
                history.append(gr.ChatMessage(role="assistant",
                        content=message["message"],
                        metadata={"title": message["title"]})
                )
            yield history

    def clear_history():
        history = []
        return history



    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(clear_history, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()


# stream = stream_chat()
# for message in stream:
#     print("GOT", message)