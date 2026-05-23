import os
import json
import base64
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import re
from datetime import datetime

# Configuration
TOKEN_PATH = '/mnt/c/Warp Projects/Efforts/Ongoing/NAUTILUS/config/token.json'
OBSIDIAN_BASE = '/mnt/c/Obsidian/life/resources/AI-Ingest'
LITELLM_URL = 'http://localhost:4000/v1/chat/completions'

def clean_text(text):
    # Basic HTML strip
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def get_gmail_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, ['https://www.googleapis.com/auth/gmail.readonly'])
    return build('gmail', 'v1', credentials=creds)

def synthesize_email(subject, body):
    payload = {
        "model": "fast-pool", # Using rotating pool via LiteLLM
        "messages": [
            {"role": "system", "content": "You are a knowledge synthesizer. Summarize the email into 3 points, extract entities (tools, models), topics, and novelty (0.0-1.0). Return ONLY JSON. Format: {\"tldr_3\": [], \"entities\": [], \"topics\": [], \"novelty\": 0.5}"},
            {"role": "user", "content": f"Subject: {subject}\n\nBody: {body[:3000]}"}
        ]
    }
    try:
        response = requests.post(LITELLM_URL, json=payload, timeout=45)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        else:
            return json.dumps({"tldr_3": ["API Error", str(res_json)], "entities": [], "topics": [], "novelty": 0.0})
    except Exception as e:
        return json.dumps({"tldr_3": ["Error during synthesis", str(e)], "entities": [], "topics": [], "novelty": 0.0})

def main():
    service = get_gmail_service()
    # Find AI Ingest label
    results = service.users().labels().list(userId='me').execute()
    label_id = next(l['id'] for l in results['labels'] if l['name'].lower() == 'ai ingest')
    
    # Get ALL messages with the label (removing maxResults limit, default loop fetches batch)
    all_messages = []
    pageToken = None
    while True:
        results = service.users().messages().list(userId='me', labelIds=[label_id], pageToken=pageToken).execute()
        all_messages.extend(results.get('messages', []))
        pageToken = results.get('nextPageToken')
        if not pageToken:
            break
    
    print(f"Total messages found in label: {len(all_messages)}")
    
    for m in all_messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        headers = msg['payload']['headers']
        subject = next(h['value'] for h in headers if h['name'] == 'Subject')
        date_str = next(h['value'] for h in headers if h['name'] == 'Date')
        
        # Parse date for folder structure
        dt = datetime.strptime(date_str.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
        folder_path = os.path.join(OBSIDIAN_BASE, dt.strftime('%Y-%m'))
        os.makedirs(folder_path, exist_ok=True)
        
        # Get body
        if 'parts' in msg['payload']:
            part = msg['payload']['parts'][0]
            if 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode()
            else:
                body = "No text content"
        else:
            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode()
            
        print(f"Processing: {subject}...")
        raw_ai_response = synthesize_email(subject, clean_text(body))
        
        # Clean AI response from markdown code blocks
        clean_json_str = re.sub(r'```json\s*|\s*```', '', raw_ai_response).strip()
        
        try:
            summary_json = json.loads(clean_json_str)
        except Exception as e:
            print(f"Failed to parse JSON: {e}. Raw response: {raw_ai_response}")
            summary_json = {"tldr_3": ["Parser Error", "Check raw log"], "entities": [], "topics": [], "novelty": 0.0}
        
        # Create Markdown file
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', subject.lower()).strip('-')
        file_path = os.path.join(folder_path, f"{slug}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"---\ntitle: {subject}\ndate: {dt.isoformat()}\ntags: {summary_json.get('topics', [])}\nnovelty: {summary_json.get('novelty', 0.5)}\n---\n\n")
            f.write(f"# {subject}\n\n")
            f.write("### 📝 TL;DR\n")
            for point in summary_json.get('tldr_3', []):
                f.write(f"- {point}\n")
            f.write("\n### 🏷 Entities\n")
            try:
                # Handle potential non-string entities
                entities = [str(e) for e in summary_json.get('entities', [])]
                f.write(", ".join(entities))
            except Exception:
                f.write(str(summary_json.get('entities', [])))

            f.write("\n\n---\n*Synthetic context generated via Qwen3-8B local*")

    print("\n✅ Test complete. Check Obsidian/life/resources/AI-Ingest")

if __name__ == '__main__':
    main()
