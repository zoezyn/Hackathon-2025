import json

import redis
from email_handler import stream_emails
from thought_logging import push_to_logging


def parse_request_id(subject: str):
    if " / " in subject:
        return subject.split(" / ")[1]
    return None


def store_attachments(email: dict):
    for attachment in email['attachments']:
        with open(f"attachments/{attachment['filename']}", 'wb') as f:
            f.write(attachment['data'])
        attachment['path'] = f"attachments/{attachment['filename']}"
        attachment['data'] = None


def email_listener():
    r = redis.Redis(host='localhost', port=6379, db=0)
    for email in stream_emails():
        push_to_logging(f"New email: {email['subject']}", None, append=False)

        request_id = parse_request_id(email['subject'])
        if request_id:
            push_to_logging(f"Request ID: {request_id}", None, append=False)
            r.set(request_id, json.dumps(email))
        else:
            store_attachments(email)
            r.publish("email_listener", json.dumps(email))


email_listener()