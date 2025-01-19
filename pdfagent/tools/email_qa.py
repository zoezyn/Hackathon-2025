import random
from time import sleep
from typing import List, Dict

import redis

from email_handler import send_email
from thought_logging import push_to_logging


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


def email_request_id():
    # random hex 6 chars
    return ''.join(random.choice('0123456789ABCDEF') for _ in range(6))


def wait_for_replies(email_requests):
    r = redis.Redis(host='localhost', port=6379, db=0)
    all_ids = set(email_requests.keys())
    got_ids = set()
    print("----------------------------")
    print("WAITING FOR REPLIES")
    print("---------------------------")
    while True:
        for id in all_ids:
            if r.get(id):
                push_to_logging(f"Email {id} got reply", "Incoing Emails", append=False)
                email_requests[id]['reply'] = r.get(id)
                got_ids.add(id)
        if len(got_ids) == len(all_ids):
            break
        sleep(0.5)

    push_to_logging("All emails got reply", "Outgoing Emails", append=False)
    return email_requests


def request_information_emails_function(emails: List[Dict[str, str]]):
    email_requests = {}
    for email in emails:
        push_to_logging(f"Sending email to {email['email']}: {email}", "Outgoing Email", append=False)
        email_id = email_request_id()
        subject = email['subject'] + " / " + email_id
        send_email(email['email'], subject, email['body'])
        email_requests[email_id] = email
    wait_for_replies(email_requests)

    res = str("\n\n".join([f"To {e['email']}, {e['subject']}:\n\n{e['reply']}" for e in email_requests.values()]))
    print("TYPE OF RESULT", type(res))
    return res

