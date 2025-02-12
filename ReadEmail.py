import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']


class ReadEmail:
    def __init__(self):
        self.service = self.gmail_authenticate()

    def gmail_authenticate(self):
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

    def search_messages(self, service, query, max_results=3):
        result = service.users().messages().list(
            userId='me', q=query, maxResults=max_results).execute()
        messages = []
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result and len(messages) < max_results:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId='me', q=query,
                                                     pageToken=page_token, maxResults=max_results-len(messages)).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages[:max_results]

    def get_size_format(self, b, factor=1024, suffix="B"):
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"

    def clean(self, text):
        return "".join(c if c.isalnum() else "_" for c in text)

    def parse_parts(self, service, parts, message):
        email_data = {"attachments": []}
        if parts:
            for part in parts:
                mimeType = part.get("mimeType")
                body = part.get("body")
                data = body.get("data")
                part_headers = part.get("headers")
                if part.get("parts"):
                    nested_data = self.parse_parts(
                        service, part.get("parts"), message)
                    email_data.update(nested_data)
                if mimeType == "text/plain" and data:
                    text = urlsafe_b64decode(data).decode()
                    email_data["body"] = text
                else:
                    for part_header in part_headers:
                        part_header_name = part_header.get("name")
                        part_header_value = part_header.get("value")
                        if part_header_name == "Content-Disposition" and "attachment" in part_header_value:
                            email_data["attachments"].append(
                                "Attachment found but not saved.")
        return email_data

    def read_message(self, service, message):
        msg = service.users().messages().get(
            userId='me', id=message['id'], format='full').execute()
        payload = msg['payload']
        headers = payload.get("headers")
        parts = payload.get("parts")
        email_data = {}
        if headers:
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    email_data["from"] = value
                if name.lower() == "to":
                    email_data["to"] = value
                if name.lower() == "subject":
                    email_data["subject"] = value
                if name.lower() == "date":
                    email_data["date"] = value
        email_data.update(self.parse_parts(service, parts, message))
        return email_data


if __name__ == '__main__':
    read = ReadEmail()
    service = read.service
    results = read.search_messages(service, "quiz", max_results=2)

    print(f"Here are your {len(results)} emails.")

    message_data = {}
    for i, msg in enumerate(results):
        msg_details = read.read_message(service, msg)
        message_data[f"Email_{i+1}"] = msg_details
    print(message_data)
