# AI Support Ticket Automation

A beginner-friendly Python workflow that reads customer-support tickets from CSV, retrieves relevant guidance from a JSON knowledge base, classifies each ticket, and writes an enriched CSV with routing information and a draft response.

Built by **Omar Sullivan**, Computer Programming AAS student at Chattahoochee Technical College.

## Why I built it

I wanted to demonstrate how AI and automation can improve a real business workflow while keeping a human reviewer in control. The project combines process mapping, Python, CSV/JSON data handling, prompt design, knowledge retrieval, API integration, validation, and automated testing.

## Workflow

1. Read support tickets from a CSV file.
2. Retrieve the most relevant article from a small JSON knowledge base.
3. Classify category, priority, and sentiment.
4. Summarize the issue and draft a response.
5. Validate the result and write it to a new CSV file.
6. Require human review before any response is sent.

## Features

- Free **demo mode** that runs locally without an API key
- Optional **LLM mode** using the OpenAI Responses API
- CSV input and output pipeline
- JSON knowledge-base retrieval
- Prompt constraints and output validation
- Unit tests and GitHub Actions continuous integration
- Secure configuration through environment variables

## Project structure

```text
ai-support-ticket-automation/
├── .github/workflows/tests.yml
├── data/
│   ├── knowledge_base.json
│   └── sample_tickets.csv
├── output/
├── tests/test_app.py
├── .env.example
├── .gitignore
├── app.py
├── requirements.txt
└── README.md
```

## Run free demo mode

Python 3.10 or later is recommended.

```bash
python app.py
```

The enriched file will be written to `output/triaged_tickets.csv`.

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Run with an LLM API

Install the dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="your-key-here"
python app.py --use-ai
```

Never put a real API key in source code, screenshots, or GitHub. API usage may incur charges. The official OpenAI quickstart explains API keys and the Python SDK: https://developers.openai.com/api/docs/quickstart

## Skills demonstrated

Python • workflow automation • LLM API integration • prompt engineering • REST concepts • JSON • CSV • data pipelines • retrieval-augmented context • validation • testing • GitHub Actions

## Responsible design

This demonstration uses fictional customer data. Draft responses are not sent automatically, refunds are not promised, and a human remains responsible for reviewing every result.

## Next improvements

- Replace keyword retrieval with vector embeddings
- Add a web interface or webhook endpoint
- Connect the workflow to n8n, Make, or Zapier
- Add evaluation data and measure classification accuracy
- Add voice-note transcription for multimodal intake
