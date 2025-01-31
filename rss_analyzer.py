import feedparser
import google.generativeai as genai
from collections import Counter
from datetime import datetime
import json
from jinja2 import Template
import markdown2
import os
import time
import re
from bs4 import BeautifulSoup
from google.api_core import exceptions

# Configure Gemini API
config_file_path = "config.json"
try:
    with open(config_file_path, "r") as f:
        config = json.load(f)
        GOOGLE_API_KEY = config.get("google_api_key")
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
except json.JSONDecodeError:
    raise json.JSONDecodeError(f"Invalid JSON in configuration file: {config_file_path}")

if not GOOGLE_API_KEY:
    raise ValueError("google_api_key not found in configuration file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def clean_html_content(html_content):
    """Clean and structure HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Supprimer les balises script et style
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extraire le texte
    text = soup.get_text()
    
    # Nettoyer le texte
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def extract_sections(content):
    """Extract different sections from the content"""
    sections = {
        'twitter_recap': [],
        'reddit_recap': [],
        'discord_recap': [],
        'detailed_summaries': []
    }
    
    current_section = None
    
    for line in content.split('\n'):
        if 'AI Twitter Recap' in line:
            current_section = 'twitter_recap'
        elif 'AI Reddit Recap' in line:
            current_section = 'reddit_recap'
        elif 'AI Discord Recap' in line:
            current_section = 'discord_recap'
        elif 'PART 1: High level Discord summaries' in line:
            current_section = 'high_level_summaries'
        elif 'PART 2: Detailed by-Channel summaries and links' in line:
            current_section = 'detailed_summaries'
        elif current_section and line.strip():
            sections[current_section].append(line.strip())
    
    return sections

def fetch_rss_feed(url):
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(url)
        processed_entries = []
        
        for entry in feed.entries:
            # Nettoyer et structurer le contenu HTML
            if hasattr(entry, 'description'):
                clean_description = clean_html_content(entry.description)
                sections = extract_sections(clean_description)
                
                processed_entry = {
                    'title': entry.title,
                    'link': entry.link,
                    'clean_description': clean_description,
                    'sections': sections
                }
                processed_entries.append(processed_entry)
        
        return processed_entries
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return []

def analyze_chunk(entries_chunk, chunk_number):
    """Analyze a chunk of entries"""
    # Préparer le contenu de manière structurée
    content = []
    for entry in entries_chunk:
        content.append(f"Title: {entry['title']}")
        
        if entry['sections']:
            for section_name, section_content in entry['sections'].items():
                if section_content:
                    content.append(f"\n{section_name.upper()}:")
                    content.append("\n".join(section_content[:5]))  # Limiter à 5 éléments par section
        
    content = "\n\n".join(content)
    
    prompt = f"""Analyze these AI news articles and provide a structured analysis.
    Focus on the most important information from each section (AI Twitter Recap, AI Reddit Recap, AI Discord Recap,PART 1: High level Discord summaries, PART 2: Detailed by-Channel summaries and links).
    
    Categories:
    1. Top News (Most important and frequently mentioned topics)
       - Major announcements and breakthroughs
       - High-impact developments
       - Industry-changing news
    
    2. High-Level News (Strategic and industry-wide impact)
       - Community trends and patterns
       - Platform updates and changes
       - Notable discussions
    
    3. Low-Level News (Technical details and smaller updates)
       - Technical discussions
       - Minor updates
       - Community interactions

    Please format the response in markdown with clear sections and subsections.
    Use bullet points for better readability.
    This is chunk {chunk_number} of the analysis.

    News to analyze:
    {content}"""

    max_retries = 3
    retry_delay = 5
    chunk_size = len(entries_chunk)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                print(f"API quota exceeded for chunk size {chunk_size}. Retrying with smaller chunk...")
                if chunk_size > 1:
                    mid = chunk_size // 2
                    first_half = analyze_chunk(entries_chunk[:mid], f"{chunk_number}a")
                    time.sleep(retry_delay)
                    second_half = analyze_chunk(entries_chunk[mid:], f"{chunk_number}b")
                    return f"{first_half}\n\n{second_half}"
                else:
                    print(f"API quota exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
            else:
                return "# Analysis Error\nUnable to analyze content due to API quota limits. Please try again later."
        except Exception as e:
            print(f"Error during analysis: {e}")
            return f"# Analysis Error\nAn error occurred during analysis: {str(e)}"

def categorize_news(entries):
    """Categorize news using Gemini AI"""
    if not entries:
        return "No entries to analyze"

    chunk_size = 5  # Réduit à 5 pour gérer la complexité
    results = []
    
    for i in range(0, len(entries), chunk_size):
        chunk = entries[i:i + chunk_size]
        chunk_result = analyze_chunk(chunk, i // chunk_size + 1)
        results.append(chunk_result)
        time.sleep(2)
    
    combined_results = "\n\n".join(results)
    
    summary_prompt = f"""Based on the following analysis results, provide a comprehensive executive summary.
    
    Please include:
    1. Key Trends and Patterns
       - Major technological developments
       - Industry shifts
       - Market impacts
    
    2. Critical Analysis
       - Interconnections between different news items
       - Potential long-term implications
       - Industry challenges and opportunities
    
    3. Future Outlook
       - Predicted developments
       - Areas to watch
       - Potential risks and opportunities
    
    Format the response in markdown with clear sections and bullet points.
    Make it detailed but concise.

    Analysis to summarize:
    {combined_results}"""
    
    try:
        summary_response = model.generate_content(summary_prompt)
        return f"{summary_response.text}\n\n{combined_results}"
    except:
        return combined_results

def generate_html_report(markdown_content):
    """Convert the markdown content to HTML"""
    # Configuration de markdown2 avec des extras
    markdown_extras = [
        "fenced-code-blocks",
        "tables",
        "header-ids",
        "break-on-newline",
        "cuddled-lists",
        "markdown-in-html"
    ]
    
    # Conversion du markdown en HTML
    html_content = markdown2.markdown(markdown_content, extras=markdown_extras)
    
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI News Analysis Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px;
                line-height: 1.6;
                background-color: #f5f6fa;
                color: #2c3e50;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            h2 {
                color: #34495e;
                margin-top: 40px;
                padding-bottom: 10px;
                border-bottom: 2px solid #eee;
                font-size: 1.8em;
            }
            h3 {
                color: #2980b9;
                margin-top: 25px;
                font-size: 1.4em;
            }
            .timestamp {
                color: #7f8c8d;
                font-size: 1em;
                margin-bottom: 30px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            .error {
                color: #e74c3c;
                padding: 15px;
                border: 1px solid #e74c3c;
                border-radius: 4px;
                margin: 15px 0;
                background-color: #fdf0f0;
            }
            .chunk {
                border-left: 4px solid #3498db;
                padding: 20px;
                margin: 25px 0;
                background-color: #f8f9fa;
                border-radius: 0 4px 4px 0;
            }
            ul {
                padding-left: 20px;
                list-style-type: disc;
            }
            ul ul {
                list-style-type: circle;
            }
            ul ul ul {
                list-style-type: square;
            }
            li {
                margin: 8px 0;
                line-height: 1.6;
            }
            .summary {
                background-color: #ebf5fb;
                padding: 25px;
                border-radius: 8px;
                margin: 30px 0;
                border: 1px solid #3498db;
            }
            .summary h2 {
                color: #2980b9;
                border-bottom: none;
                margin-top: 0;
            }
            .category {
                margin: 20px 0;
                padding: 15px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            code {
                background-color: #f7f9fa;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Consolas', monospace;
                font-size: 0.9em;
            }
            pre {
                background-color: #f7f9fa;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                margin: 15px 0;
                padding: 10px 20px;
                background-color: #f8f9fa;
                color: #34495e;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI News Analysis Report</h1>
            <div class="timestamp">Generated on: {{ timestamp }}</div>
            <div class="summary">
                {{ content|safe }}
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(template_str)
    final_html = template.render(
        content=html_content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    with open("news_report.html", "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    # RSS feed URL
    rss_url = "https://buttondown.com/ainews/rss"
    
    # Fetch RSS entries
    print("Fetching RSS feed...")
    entries = fetch_rss_feed(rss_url)
    
    if not entries:
        print("Error: No entries found in the RSS feed")
        return
    
    # Analyze and categorize news
    print("Analyzing content with Gemini...")
    categorized_content = categorize_news(entries)
    
    # Generate HTML report
    print("Generating HTML report...")
    generate_html_report(categorized_content)
    print("Report generated as news_report.html")

if __name__ == "__main__":
    main() 