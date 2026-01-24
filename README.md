# Freshdesk Feedback AI Analysis System

A Python-based system for analyzing customer feedback from Freshdesk using AI-powered insights.

## Project Overview

This system fetches customer feedback data from Freshdesk, processes it using AI analysis, and generates comprehensive reports to help improve customer satisfaction and identify key trends.

## Project Structure

```
cs feedbacks/
├── context/              # Context files and configuration for AI analysis
├── data/
│   ├── raw/             # Raw data fetched from Freshdesk API
│   └── processed/       # Cleaned and processed feedback data
├── reports/
│   ├── markdown/        # Generated reports in Markdown format
│   └── json/            # Generated reports in JSON format
├── src/                 # Source code and modules
├── .env                 # Environment variables (not tracked in git)
├── .env.example         # Example environment variables template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Freshdesk account with API access
- OpenAI API key

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd "cs feedbacks"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:
```
FRESHDESK_API_KEY=your_freshdesk_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Getting API Keys

#### Freshdesk API Key
1. Log in to your Freshdesk account
2. Click on your profile picture (top right)
3. Go to Profile Settings
4. Your API key is displayed in the right sidebar under "Your API Key"

#### OpenAI API Key
1. Visit https://platform.openai.com/
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new secret key and copy it

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FRESHDESK_API_KEY` | Your Freshdesk API key for accessing tickets and feedback | Yes |
| `FRESHDESK_DOMAIN` | Your Freshdesk domain (e.g., yourcompany.freshdesk.com) | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key for AI-powered analysis | Yes |

## Usage

### Run the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run main application
python main.py
```

The complete analysis pipeline follows 8 steps:

1. **Input Collection** - Interactive CLI prompts for parameters
2. **Cache Check** - Check for existing data (avoid redundant API calls)
3. **Fetch from Freshdesk** - ONLY called on cache miss (strict filtering + pagination)
4. **Data Cleaning** - Remove noise, extract meaningful feedback
5. **Load Game Context** - Load features, constraints, recent changes from YAML
6. **AI Classification** - OpenAI GPT-4 analysis with game context (user confirmation required)
7. **Pattern Aggregation** - Group by category/feature/sentiment, detect trends
8. **Report Generation** - Create Markdown and JSON reports

**Critical:** Freshdesk API is called ONLY on cache miss, saving time and API quota.

See [PIPELINE.md](PIPELINE.md) for detailed pipeline documentation.

### Test Individual Components

```bash
# Test input handler
python test_input_handler.py

# Test storage manager
python test_storage_manager.py

# Test Freshdesk client
python test_freshdesk_client.py

# Test context loader
python test_context_loader.py

# Test data cleaner
python test_data_cleaner.py

# Test individual modules
python -m src.input_handler
python -m src.storage_manager
python -m src.freshdesk_client
python -m src.context_loader
python -m src.data_cleaner
```

### Documentation

- **[USAGE.md](USAGE.md)** - Interactive input handler guide
- **[STORAGE.md](STORAGE.md)** - Storage manager and caching documentation
- **[FRESHDESK_API.md](FRESHDESK_API.md)** - Freshdesk API client documentation
- **[CONTEXT.md](CONTEXT.md)** - Game context loader documentation
- **[PIPELINE.md](PIPELINE.md)** - Complete pipeline flow and orchestration
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Write descriptive docstrings for all functions and classes
- Keep functions focused and modular

### Testing
*Testing framework to be added*

## Security Notes

⚠️ **IMPORTANT**: Never commit your `.env` file to version control. The `.env` file contains sensitive API keys and should remain local to your machine.

- `.env` is included in `.gitignore`
- Use `.env.example` as a template for required variables
- Rotate your API keys immediately if they are accidentally exposed

## Features

### ✅ Implemented

- **Interactive CLI Input Handler** - Collects game name, OS, and date range with validation
- **Storage Manager** - Caching system with deterministic filenames and cache hit/miss logging
- **Freshdesk API Client** - Fetches feedback tickets with strict filtering and pagination
- **Game Context Loader** - Loads game features, constraints, and recent changes from YAML
- **Data Cleaner** - Removes auto-replies, signatures, HTML, and noise from feedback
- **AI Classifier** - OpenAI-powered per-ticket classification with game context
- **Aggregator** - Groups and analyzes classified tickets to identify patterns and trends
- **Report Generator** - Creates Markdown reports for designers and JSON exports
- **Configuration Management** - Environment variable handling with validation
- **Logging System** - Colored console output and file logging
- **Utility Functions** - Common helpers for file operations and data handling

### 📋 To Be Implemented

- OpenAI analysis integration
- Report generation (Markdown & JSON)
- Automated scheduling
- Comprehensive testing suite
- Deployment configuration

## Project Roadmap

- [x] Project structure setup
- [x] Interactive input collection
- [x] Data caching/storage system
- [x] Freshdesk API integration
- [x] Data fetching with strict filtering
- [x] Game context loading from YAML
- [x] Data cleaning and noise removal
- [x] AI-powered ticket classification
- [x] Pattern detection and trend analysis
- [x] Report generation (Markdown & JSON)
- [x] Complete end-to-end analysis pipeline
- [ ] Report generation
- [ ] Automated scheduling
- [ ] Testing suite
- [ ] Deployment configuration

## License

*To be determined*

## Contributing

*Contribution guidelines to be added*

## Support

For issues and questions, please create an issue in the project repository.
