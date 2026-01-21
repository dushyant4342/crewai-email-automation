# CrewAI Email Reading and Draft Generation System

A multi-agent system built with CrewAI that reads emails and automatically generates professional draft responses. The system processes the first two emails from your inbox and creates draft responses using AI agents.

## Features

- **Email Reading Agent**: Analyzes emails to extract key information, sender details, and main points
- **Draft Generation Agent**: Creates professional email draft responses based on the analysis
- **IMAP Email Integration**: Fetches emails directly from your email inbox
- **Gmail Draft Creation**: Automatically creates drafts in your Gmail Drafts folder
- **Limited Processing**: Processes only the first 2 emails (configurable)

## Project Structure

```
poc-crewai/
├── agents/
│   ├── email_reader.py      # Email reading agent
│   └── draft_generator.py   # Draft generation agent
├── tasks/
│   └── email_tasks.py       # Task definitions
├── crew/
│   └── email_crew.py        # Crew orchestration
├── utils/
│   ├── email_fetcher.py     # Email fetching utilities
│   └── draft_creator.py     # Gmail draft creation utilities
├── main.py                  # Main execution script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your details:

```env
# OpenAI API Key (required for LLM)
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (IMAP)
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
```

**Note for Gmail users:**
- You may need to use an "App Password" instead of your regular password
- Enable 2-factor authentication
- Generate an app password from your Google Account settings

### 3. Run the System

```bash
python main.py
```

## How It Works

1. **Email Fetching**: The system connects to your email via IMAP and fetches the first 2 unread emails
2. **Email Analysis**: The Email Reader agent analyzes each email to understand:
   - Sender information
   - Main purpose and intent
   - Key points to address
   - Tone and urgency level
3. **Draft Generation**: The Draft Generator agent creates a professional response draft based on the analysis
4. **Draft Creation**: Drafts are automatically created in your Gmail Drafts folder and can be reviewed/sent from Gmail

## Agents

### Email Reader Agent
- **Role**: Email Reader
- **Goal**: Read and analyze emails to extract key information
- **Responsibilities**: Extract sender details, identify main purpose, summarize key points, assess tone and urgency

### Draft Generator Agent
- **Role**: Email Draft Writer
- **Goal**: Generate professional email draft responses
- **Responsibilities**: Create clear, concise, and appropriate responses that address all points from the original email

## Customization

### Change Number of Emails

Edit `main.py` to change the limit:

```python
emails = fetch_emails(limit=5)  # Process 5 emails instead of 2
```

### Change Email Search Criteria

Edit `utils/email_fetcher.py` to change the search criteria:

```python
# Change from 'UNSEEN' to 'ALL' to process all emails
status, messages = mail.search(None, 'ALL')
```

### Modify Agent Behavior

Edit the agent files in `agents/` to customize:
- Agent roles and goals
- Backstories
- LLM models and temperature settings

## Requirements

- Python 3.8+
- OpenAI API key
- Email account with IMAP access enabled
- Internet connection

## Troubleshooting

### Email Connection Issues
- Verify your email credentials are correct
- Check that IMAP is enabled in your email settings
- For Gmail, use an App Password instead of your regular password
- Verify firewall settings allow IMAP connections

### OpenAI API Issues
- Ensure your API key is valid and has credits
- Check your API usage limits
- Verify the API key is correctly set in `.env`

## License

This project is a proof of concept demonstration of CrewAI multi-agent systems.


# crewai-email-automation
