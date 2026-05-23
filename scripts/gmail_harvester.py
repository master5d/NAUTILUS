import os.path
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    """Shows basic usage of the Gmail API.
    Lists the labels in the user's account.
    """
    creds = None
    cred_path = '/mnt/c/Warp Projects/Efforts/Ongoing/NAUTILUS/config/credentials.json'
    token_path = '/mnt/c/Warp Projects/Efforts/Ongoing/NAUTILUS/config/token.json'

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            # Use fixed port and no local server as we are in WSL and want a clear link
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # 1. First, let's find the ID for the label "AI Ingest"
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    ai_ingest_label_id = None
    for label in labels:
        if label['name'].lower() == 'ai ingest':
            ai_ingest_label_id = label['id']
            break

    if not ai_ingest_label_id:
        print("Error: Label 'AI Ingest' not found in your Gmail.")
        return

    print(f"Found 'AI Ingest' label (ID: {ai_ingest_label_id}). Scanning messages...")

    # 2. Fetch list of messages with this label
    results = service.users().messages().list(userId='me', labelIds=[ai_ingest_label_id]).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found with label AI Ingest.')
    else:
        print(f"Total messages to process: {len(messages)}")
        for message in messages[:10]: # Print first 10 for dry run
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
            headers = msg['payload']['headers']
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            print(f"- {subject}")

if __name__ == '__main__':
    main()
