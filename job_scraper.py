"""
Job Scraper - Scrapes Indeed & LinkedIn for job listings and sends email notifications
Author: Logan Blaesing
 
See README for setup instructions

"""
 
import requests
from bs4 import BeautifulSoup
import smtplib
import json
import os
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
 
# ─────────────────────────────────────────────
# Congif Files
# ─────────────────────────────────────────────
 
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password_here"  
EMAIL_RECEIVER = "your_email@gmail.com"
 
# Job search terms — customize these
SEARCH_QUERIES = [
    "backend software engineer",
    "node.js developer",
    "full stack developer",
    "software engineer",
]
 
LOCATION = "remote"  # e.g. "remote", "Chicago IL", "Saint Louis MO"
 
# File to track jobs we've already seen
SEEN_JOBS_FILE = "seen_jobs.json"
 
# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────
 
def load_seen_jobs():
    """Load previously seen job IDs from disk."""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()
 
 
def save_seen_jobs(seen_jobs):
    """Save seen job IDs to disk."""
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)
 
 
def send_email(new_jobs):
    """Send an HTML email with new job listings."""
    if not new_jobs:
        print("No new jobs to send.")
        return
 
    print(f"Sending email with {len(new_jobs)} new job(s)...")
 
    # Build HTML email body
    job_rows = ""
    for job in new_jobs:
        job_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <strong>{job['title']}</strong><br>
                <span style="color: #555;">{job['company']}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; color: #555;">
                {job['location']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">
                <a href="{job['url']}" style="color: #2563eb;">View Job</a>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; color: #888; font-size: 12px;">
                {job['source']}
            </td>
        </tr>
        """
 
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1e293b;">🎯 {len(new_jobs)} New Job Listing(s) Found</h2>
        <p style="color: #555;">Here are the latest matches from your job scraper — {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <thead>
                <tr style="background: #f1f5f9;">
                    <th style="padding: 12px; text-align: left;">Job Title & Company</th>
                    <th style="padding: 12px; text-align: left;">Location</th>
                    <th style="padding: 12px; text-align: left;">Link</th>
                    <th style="padding: 12px; text-align: left;">Source</th>
                </tr>
            </thead>
            <tbody>
                {job_rows}
            </tbody>
        </table>
        <p style="color: #aaa; font-size: 12px; margin-top: 30px;">Sent by your job scraper script. Good luck, Logan! 🚀</p>
    </body>
    </html>
    """
 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(new_jobs)} New Job(s) Found — {datetime.now().strftime('%b %d')}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html, "html"))
 
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
 
 
# ─────────────────────────────────────────────
# Scrapers
# ─────────────────────────────────────────────
 
def scrape_indeed(query, location):
    """Scrape Indeed for job listings."""
    jobs = []
    headers = {
        #create a "real browser" signature to prevent Indeed from blocking requests
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    #Format the search to replaces spaces with + as Indeed uses that in their URL
    formatted_query = query.replace(" ", "+")
    formatted_location = location.replace(" ", "+")
    url = f"https://www.indeed.com/jobs?q={formatted_query}&l={formatted_location}&sort=date"
 
    try:
        #Fetches raw HTML, then Beautiful Soup parses into something to navigate
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        #Indeed uses job_seen_beacon to wrap each listing. This finds all of the divs on the page to query
        job_cards = soup.find_all("div", class_="job_seen_beacon")
 
        for card in job_cards[:10]:  #Fetches job Title, company, location, and a link and strips them to be sent. Set a limit of the top 10 searches per query to test. 
            try:
                title_el = card.find("span", {"id": lambda x: x and "jobTitle" in x})
                company_el = card.find("span", {"data-testid": "company-name"})
                location_el = card.find("div", {"data-testid": "text-location"})
                link_el = card.find("a", {"id": lambda x: x and "job_" in str(x)})
 
                title = title_el.get_text(strip=True) if title_el else "N/A"
                company = company_el.get_text(strip=True) if company_el else "N/A"
                loc = location_el.get_text(strip=True) if location_el else "N/A"
                job_url = "https://www.indeed.com" + link_el["href"] if link_el else url
                #Creates a unique ID so I do not see the same job twice
                job_id = f"indeed_{title}_{company}".lower().replace(" ", "_")
 
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": loc,
                    "url": job_url,
                    "source": "Indeed"
                })
            except Exception:
                continue
 
    except Exception as e:
        print(f"Indeed scrape error for '{query}': {e}")
 
    return jobs
 
 
def scrape_linkedin(query, location):
    """Scrape LinkedIn public job listings."""
    jobs = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    #Same with Indeed, Linkedin spaces their URLs uniquely
    formatted_query = query.replace(" ", "%20")
    formatted_location = location.replace(" ", "%20")
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={formatted_query}&location={formatted_location}&sortBy=DD"
    )
 
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
 
        job_cards = soup.find_all("div", class_="base-card")
 
        for card in job_cards[:10]: #Same structure as Linkedin Function but for Indeed
            try:
                title_el = card.find("h3", class_="base-search-card__title")
                company_el = card.find("h4", class_="base-search-card__subtitle")
                location_el = card.find("span", class_="job-search-card__location")
                link_el = card.find("a", class_="base-card__full-link")
 
                title = title_el.get_text(strip=True) if title_el else "N/A"
                company = company_el.get_text(strip=True) if company_el else "N/A"
                loc = location_el.get_text(strip=True) if location_el else "N/A"
                job_url = link_el["href"] if link_el else url
      
                job_id = f"linkedin_{title}_{company}".lower().replace(" ", "_")
 
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": loc,
                    "url": job_url,
                    "source": "LinkedIn"
                })
            except Exception:
                continue
 
    except Exception as e:
        print(f"LinkedIn scrape error for '{query}': {e}")
 
    return jobs
 
 
# ─────────────────────────────────────────────
# Scraper Jobs
# ─────────────────────────────────────────────
 
def run_scraper():
    #Scrapes jobs, filters them, and prevents old ones from being sent again.
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running job scraper...")
 
    seen_jobs = load_seen_jobs()
    all_jobs = []
 
    for query in SEARCH_QUERIES:
        print(f"  Scraping Indeed for: '{query}'...")
        all_jobs += scrape_indeed(query, LOCATION)
 
        print(f"  Scraping LinkedIn for: '{query}'...")
        all_jobs += scrape_linkedin(query, LOCATION)
 
    # Filter to only new jobs
    new_jobs = [job for job in all_jobs if job["id"] not in seen_jobs]
 
    # Deduplicate jobs by ID to ensure it's unique
    seen_this_run = set()
    unique_new_jobs = []
    for job in new_jobs:
        if job["id"] not in seen_this_run:
            unique_new_jobs.append(job)
            seen_this_run.add(job["id"])
 
    print(f"  Found {len(unique_new_jobs)} new job(s).")
 
    # Send email if there are new jobs
    send_email(unique_new_jobs)
 
    # Update seen jobs
    for job in unique_new_jobs:
        seen_jobs.add(job["id"])
    save_seen_jobs(seen_jobs)
 
 
# ─────────────────────────────────────────────
# Main Function
# ─────────────────────────────────────────────
 
if __name__ == "__main__":
    print("Job scraper started!")
    print(f"Searching for: {SEARCH_QUERIES}")
    print(f"Location: {LOCATION}")
    print(f"Sending results to: {EMAIL_RECEIVER}")
 
    
    run_scraper()
