"""Utility functions for fetching emails via IMAP"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

def decode_mime_words(s):
    """Decode MIME encoded words"""
    if s is None:
        return ""
    decoded = decode_header(s)
    return ''.join([text.decode(encoding or 'utf-8', errors='ignore') if isinstance(text, bytes) else text 
                    for text, encoding in decoded])

def fetch_emails(limit: int = 2) -> List[Dict]:
    """
    Fetch emails from IMAP server
    
    Args:
        limit: Maximum number of emails to fetch (default: 2)
    
    Returns:
        List of email dictionaries with 'from', 'subject', 'date', 'body' keys
    """
    # Get email configuration from environment
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    imap_server = os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
    imap_port = int(os.getenv('EMAIL_IMAP_PORT', '993'))
    
    if not email_address or not email_password:
        raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
    
    emails = []
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, email_password)
        mail.select('inbox')
        
        # Search for all emails in inbox (latest first)
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK':
            print("No emails found or error occurred")
            return emails
        
        # Get list of email IDs
        email_ids = messages[0].split()
        
        # Reverse to get latest emails first (IMAP returns oldest first)
        email_ids.reverse()
        
        # Limit to first N emails (now the latest N)
        email_ids = email_ids[:limit] if len(email_ids) >= limit else email_ids
        
        # Fetch each email
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                continue
            
            # Parse email
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract email details
            email_dict = {
                'from': decode_mime_words(email_message['From']),
                'subject': decode_mime_words(email_message['Subject']),
                'date': email_message['Date'],
                'message_id': email_message.get('Message-ID', ''),
                'references': email_message.get('References', ''),
                'in_reply_to': email_message.get('In-Reply-To', ''),
                'body': ''
            }
            
            # Extract body
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            email_dict['body'] = body
                            break
                        except:
                            pass
            else:
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_dict['body'] = body
                except:
                    email_dict['body'] = str(email_message.get_payload())
            
            emails.append(email_dict)
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        raise
    
    return emails

