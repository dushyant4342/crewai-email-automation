"""Main script to run the email reading and draft generation system"""
import os
import sys
from dotenv import load_dotenv
from utils.email_fetcher import fetch_emails
from utils.draft_creator import create_gmail_draft
from crew.email_crew import process_email

# Fix encoding for Windows console to handle emoji and special characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

def main():
    """Main function to fetch emails and generate drafts"""
    print("=" * 60)
    print("Email Reading and Draft Generation System")
    print("=" * 60)
    print()
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not found in .env file")
        print("Please set your OpenAI API key in the .env file")
        return
    
    # Fetch first 2 emails
    print("Fetching emails...")
    try:
        emails = fetch_emails(limit=2)
        
        if not emails:
            print("No emails found to process.")
            return
        
        print(f"Found {len(emails)} email(s) to process.\n")
        
        # Process each email
        for idx, email_data in enumerate(emails, 1):
            print(f"\n{'='*60}")
            print(f"Processing Email {idx} of {len(emails)}")
            print(f"{'='*60}")
            print(f"From: {email_data['from']}")
            print(f"Subject: {email_data['subject']}")
            print(f"Date: {email_data['date']}")
            print(f"\nOriginal Email Content:")
            print("-" * 60)
            print(email_data['body'][:500] + "..." if len(email_data['body']) > 500 else email_data['body'])
            print("-" * 60)
            print("\nGenerating draft response...\n")
            
            try:
                # Process email and generate draft
                draft_result = process_email(email_data)
                
                print(f"\n{'='*60}")
                print(f"Generated Draft for Email {idx}")
                print(f"{'='*60}")
                print(draft_result)
                print(f"{'='*60}\n")
                
                # Create draft in Gmail
                try:
                    create_gmail_draft(str(draft_result), email_data)
                    print(f"✓ Draft created successfully in Gmail Drafts folder!\n")
                except Exception as draft_error:
                    print(f"⚠ Warning: Could not create draft in Gmail: {str(draft_error)}")
                    print("Draft content displayed above for manual copy.\n")
                
            except Exception as e:
                print(f"Error processing email {idx}: {str(e)}")
                continue
        
        print("\n" + "=" * 60)
        print("Processing complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease check your email configuration in .env file:")
        print("- EMAIL_ADDRESS")
        print("- EMAIL_PASSWORD")
        print("- EMAIL_IMAP_SERVER (optional, defaults to imap.gmail.com)")
        print("- EMAIL_IMAP_PORT (optional, defaults to 993)")

if __name__ == "__main__":
    main()

