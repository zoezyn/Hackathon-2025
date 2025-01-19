import json

import redis
from email_handler import stream_emails, send_email
from functions import questions_from_pdf, fill_responses_to_pdf
from pdfagent.process_with_attachment import process_with_attachment
from pdfagent.process_without_attachment import process_without_attachment
from thought_logging import push_to_logging
from time import sleep


def analyze_attachment(attachment):
    res = questions_from_pdf(attachment['path'])
    res['path'] = attachment['path']
    print(res)
    return res

    # push_to_logging(f"Analyzing attachment: {attachment['filename']}", None, append=True)
    #
    # # sleep(1)
    #
    # questions = {
    #     'questions': [
    #         {'id': 'q1', 'question': 'What is the name of the company?', 'context': None},
    #         {'id': 'q2', 'question': 'What is the name of the contact person?', 'context': None},
    #         {'id': 'q3', 'question': 'VAT number of the company'},
    #     ]
    # }
    #
    # push_to_logging(f"Questions: {json.dumps(questions)}", None, append=True)
    # return questions


def stream_email_requests():
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('email_listener')
    for message in pubsub.listen():
        print("GOT EMAIL", message)
        if message['type'] == 'message':
            try:
                msg = json.loads(message['data'].decode('utf-8'))
                yield msg
            except Exception as e:
                print("ERROR", e)
                msg = message['data']


# def agent():
#     for email in stream_email_requests():
#         push_to_logging(f"Processing email: {json.dumps(email, indent=2)}", None, append=False)
#         if len(email['attachments']) > 0:
#             push_to_logging(f"Has attachment, analyzing...", None, append=False)
#             for attachment in email['attachments']:
#                 push_to_logging(f"Attachment: {attachment['filename']}", None, append=True)
#                 attachment_data = analyze_attachment(attachment)

#                 push_to_logging(f"Attachment data: {attachment_data}", None, append=True)
#                 PDFAgent().process_with_attachment(email, attachment_data)
#                 push_to_logging(f"PDF processed", None, append=True)
#         else:
#             PDFAgent().process_without_attachment(email)


# agent()


def send_reply(email, reply):
    send_email(email['from'], f"Re: {email['subject']}", reply['body'], attachments=reply['attachments'])
    push_to_logging(email['body'], f"Email To {email['from']}: Re: {email['subject']}", append=False)




# email = {"subject": "Hey could you fill this for me?", "from": "Vadim Lobanov <vadim@lobanov.pw>", "date": "Sun, 19 Jan 2025 12:11:39 +0100", "body": "Really need this customs form filled\\r\\n", "attachments": [{"filename": "dhl-express-importanweisung-filled.pdf", "data": None, "content_type": "application/pdf", "path": "attachments/dhl-express-importanweisung-filled.pdf"}], "id": "12"}
# for attachment in email['attachments']:
#     attachment_data = analyze_attachment(attachment)
#     res = process_with_attachment(email, attachment_data)
#
#     print(res)


res = [
    {"id": "cedea29d-cdbb-38c9-a5b0-06ae588c3e1a", "answer": "12929921"}
]

# input = questions_from_pdf("attachments/dhl-express-importanweisung-verzollung-en.pdf")
# print(input)
# print(fill_responses_to_pdf("attachments/dhl-express-importanweisung-verzollung-en.pdf", {'questions': res}))


for email in stream_email_requests():
    push_to_logging(f"Processing email: {json.dumps(email, indent=2)}", None, append=False)
    if len(email['attachments']) > 0:
        push_to_logging(f"Has attachment, analyzing...", None, append=False)
        for attachment in email['attachments']:
            push_to_logging(f"Attachment: {attachment['filename']}", None, append=True)
            attachment_data = analyze_attachment(attachment)

            push_to_logging(f"Attachment data: {attachment_data}", None, append=True)
            send_reply(email, process_with_attachment(email, attachment_data))
            push_to_logging(f"PDF processed", None, append=True)
    else:
        send_reply(email, process_without_attachment(email))
