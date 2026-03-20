# Job Scraper

A Python automation script that scrapes Indeed and LinkedIn for job listings matching custom search queries, filters out previously seen results, and sends a formatted HTML email digest daily.

## Features
- Scrapes Indeed and LinkedIn simultaneously
- Filters out previously seen jobs so you only get new listings
- Sends a clean HTML email with job title, company, location, and link
- Runs on a 24 hour schedule or manually on demand

## Setup

### 1. Install dependencies
pip install requests beautifulsoup4 schedule

### 2. Configure the script
Open job_scraper.py and fill in the CONFIG section at the top:
- EMAIL_SENDER — your Gmail address
- EMAIL_PASSWORD — your Gmail App Password
- EMAIL_RECEIVER — where to send results
- SEARCH_QUERIES — customize your job search terms
- LOCATION — e.g. "remote", "Chicago IL"

### 3. Gmail App Password
- Go to myaccount.google.com
- Security → 2-Step Verification → App Passwords
- Generate a new "App Password" by filling in the App name and pressing "create"

## Usage
python job_scraper.py

## Built With
- Python
- requests
- BeautifulSoup4
- smtplib
- schedule
