"""Utility functions for creating email drafts in Gmail"""
import imaplib
import email
from email.mime.text import MIMEText
from email.header import Header
import re
import os
from dotenv import load_dotenv

load_dotenv()

def extract_email_address(text):
    """Extract email address from text like 'Name <email@example.com>' or 'email@example.com'"""
    # Try to find email in angle brackets first
    match = re.search(r'<([^>]+)>', text)
    if match:
        return match.group(1)
    # Otherwise, try to find a valid email pattern
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if match:
        return match.group(0)
    return None

def parse_draft_content(draft_text, original_email):
    """
    Parse the generated draft to extract subject, body, and recipient
    
    Args:
        draft_text: The generated draft text from the agent
        original_email: Original email dict with 'from' field
    
    Returns:
        Dictionary with 'to', 'subject', 'body'
    """
    # Extract recipient from original email
    to_email = extract_email_address(original_email.get('from', ''))
    
    # Try to extract subject from draft (look for "Subject:" line)
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', draft_text, re.IGNORECASE | re.MULTILINE)
    if subject_match:
        subject = subject_match.group(1).strip()
    else:
        # Default to Re: original subject
        original_subject = original_email.get('subject', '')
        subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
    
    # Ensure subject always starts with "Re: " for proper threading (unless it already does)
    if subject and not subject.upper().startswith('RE:'):
        # Remove any existing "Re: " and add it properly
        subject = subject.lstrip('Re: ').lstrip('RE: ').lstrip('re: ')
        subject = f"Re: {subject}"
    
    # Extract body - remove subject line if present, clean up
    body = draft_text
    # Remove subject line if found
    body = re.sub(r'Subject:\s*.+?(?:\n|$)', '', body, flags=re.IGNORECASE | re.MULTILINE)
    # Remove common headers
    body = re.sub(r'^(To|From|Date):\s*.+?(?:\n|$)', '', body, flags=re.IGNORECASE | re.MULTILINE)
    body = body.strip()
    
    return {
        'to': to_email or original_email.get('from', ''),
        'subject': subject,
        'body': body
    }

def create_gmail_draft(draft_content, original_email):
    """
    Create a draft email in Gmail using IMAP
    
    Args:
        draft_content: Dictionary with 'to', 'subject', 'body'
        original_email: Original email dict for reference
    
    Returns:
        True if successful, False otherwise
    """
    # Get email configuration from environment
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    imap_server = os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
    imap_port = int(os.getenv('EMAIL_IMAP_PORT', '993'))
    
    if not email_address or not email_password:
        raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env file")
    
    try:
        # Parse draft content
        parsed = parse_draft_content(draft_content, original_email)
        
        # Create email message
        msg = MIMEText(parsed['body'], 'plain', 'utf-8')
        msg['From'] = email_address
        msg['To'] = parsed['to']
        msg['Subject'] = Header(parsed['subject'], 'utf-8')
        
        # Add threading headers to reply to the original email (critical for Gmail threading)
        original_message_id = original_email.get('message_id', '').strip()
        original_references = original_email.get('references', '').strip()
        original_in_reply_to = original_email.get('in_reply_to', '').strip()
        
        # Always set threading headers if we have a message ID
        if original_message_id:
            # Set In-Reply-To header to link this reply to the original email
            msg['In-Reply-To'] = original_message_id
            
            # Build References header (should include original References + original Message-ID)
            # This is crucial for Gmail to thread the emails correctly
            references_parts = []
            if original_references:
                # Split existing references and add them
                ref_list = original_references.split()
                references_parts.extend(ref_list)
            if original_in_reply_to and original_in_reply_to not in ' '.join(references_parts):
                references_parts.append(original_in_reply_to)
            if original_message_id and original_message_id not in ' '.join(references_parts):
                references_parts.append(original_message_id)
            
            if references_parts:
                msg['References'] = ' '.join(references_parts)
        else:
            # If no message ID, at least ensure subject has "Re: " for basic threading
            print("Warning: No Message-ID found in original email. Threading may not work perfectly.")
        
        # Convert message to string
        message_string = msg.as_string()
        
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, email_password)
        
        # Append to Drafts folder
        # Gmail uses '[Gmail]/Drafts' or 'Drafts' depending on configuration
        try:
            mail.append('[Gmail]/Drafts', None, None, message_string.encode('utf-8'))
        except:
            # Try alternative folder name
            try:
                mail.append('Drafts', None, None, message_string.encode('utf-8'))
            except Exception as e:
                # Try to find drafts folder
                status, folders = mail.list()
                drafts_folder = None
                for folder in folders:
                    folder_str = folder.decode('utf-8')
                    if 'Draft' in folder_str or 'DRAFTS' in folder_str.upper():
                        # Extract folder name
                        drafts_folder = folder_str.split('"')[-2]
                        break
                
                if drafts_folder:
                    mail.append(drafts_folder, None, None, message_string.encode('utf-8'))
                else:
                    raise Exception(f"Could not find Drafts folder. Error: {str(e)}")
        
        mail.logout()
        return True
        
    except Exception as e:
        print(f"Error creating draft in Gmail: {str(e)}")
        raise

