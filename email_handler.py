import json
import os
import imaplib
import email
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from time import sleep
from dotenv import load_dotenv
from typing import List, Dict, Optional

from thought_logging import push_to_logging

# Load environment variables
load_dotenv()


class EmailHandler:
    def __init__(self):
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.imap_server = os.getenv('IMAP_SERVER')
        self.imap_port = int(os.getenv('IMAP_PORT', 993))
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        print(self.email_address, self.password, self.imap_server, self.imap_port, self.smtp_server, self.smtp_port)

    def fetch_emails(self, folder: str = 'INBOX', seen_email_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch emails from the specified folder, excluding any previously seen email IDs.
        
        Args:
            folder (str): Email folder to fetch from (default: 'INBOX')
            seen_email_ids (List[str], optional): List of email IDs to exclude from results
            
        Returns:
            List[Dict]: List of email dictionaries containing subject, from, date, and body
        """
        try:
            # Connect to IMAP server
            print("CONNECTING TO IMAP SERVER", self.imap_server, self.imap_port)
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_address, self.password)
            
            # Select the folder
            imap.select(folder)
            
            # Search for all emails
            _, messages = imap.search(None, 'ALL')
            email_ids = messages[0].split()
            print(email_ids)
            
            # Reverse the list to get newest emails first
            email_ids = email_ids[::-1]
            
            # Initialize seen_email_ids if None
            if seen_email_ids is None:
                seen_email_ids = []
            
            emails = []
            for email_id in email_ids:
                # Skip if we've seen this email before
                if email_id.decode() in seen_email_ids:
                    continue
                    
                _, msg_data = imap.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email content
                subject = email_message['subject']
                sender = email_message['from']
                date = email_message['date']
                body = ""
                attachments = []
                
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                        elif part.get_content_maintype() != 'multipart':
                            # This is an attachment
                            filename = part.get_filename()
                            if filename:
                                attachment_data = part.get_payload(decode=True)
                                attachments.append({
                                    'filename': filename,
                                    'data': attachment_data,
                                    'content_type': part.get_content_type()
                                })
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                emails.append({
                    'subject': subject,
                    'from': sender,
                    'date': date,
                    'body': body,
                    'attachments': attachments,
                    'id': email_id.decode()
                })
            
            imap.close()
            imap.logout()
            return emails
            
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")

    def send_email(self, to_address: str, subject: str, body: str, html_body: Optional[str] = None, attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to_address (str): Recipient email address
            subject (str): Email subject
            body (str): Plain text email body
            html_body (str, optional): HTML version of the email body
            attachments (List[str], optional): List of file paths to attach as PDFs
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_address
            
            # Add plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
                
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    with open(attachment_path, 'rb') as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                        attachment.add_header('Content-Type', 'application/pdf')
                        msg.attach(attachment)
            
            # Connect to SMTP server
            smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
            smtp.starttls()
            smtp.login(self.email_address, self.password)
            
            # Send email
            smtp.send_message(msg)
            smtp.quit()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")


def fetch_new_emails() -> List[Dict]:
    handler = EmailHandler()
    if not os.path.exists('seen_email_ids.json'):
        with open('seen_email_ids.json', 'w') as f:
            json.dump([], f)
    with open('seen_email_ids.json', 'r') as f:
        seen_email_ids = json.load(f)
    emails = handler.fetch_emails(seen_email_ids=seen_email_ids)
    new_email_ids = [*seen_email_ids, *[email['id'] for email in emails]]
    with open('seen_email_ids.json', 'w') as f:
        json.dump(new_email_ids, f)
    return emails


def stream_emails():
    while True:
        emails = fetch_new_emails()
        for email in emails:
            attachments = ""
            if len(email['attachments']) > 0:
                attachments = "\n\nAttachments:\n"
                for attachment in email['attachments']:
                    attachments += f"{attachment['filename']}\n"
            push_to_logging(f"**{email['subject']}**\n{email['body']}{attachments}", f"Email from {email['from']}")

            yield email
        sleep(5)


def send_email(to_address: str, subject: str, body: str, html_body: Optional[str] = None, attachments = []) -> bool:
    handler = EmailHandler()
    return handler.send_email(to_address, subject, body, html_body, attachments=attachments)
