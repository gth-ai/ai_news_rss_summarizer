# AI News RSS Analyzer with Gemini AI

A powerful tool that leverages Google's Gemini AI to analyze and summarize the comprehensive AI News RSS feed (ainews@buttondown.email), making it easier to digest the daily flood of AI news and developments.

## 🌟 Why This Project?

AI News (by @Smol_AI) is widely recognized as one of the best AI news newsletters, endorsed by industry leaders like Andrej Karpathy:

> "I'm not sure that enough people subscribe to the @Smol_AI newsletter. It's 1 very comprehensive email per day summarizing AI/LLM chatter across X, Reddit, Discord. There's probably others (feel free to reply), but I like this one quite a bit, ty again to @swyx and team."

However, the daily digest can be overwhelming with:
- Lengthy content across multiple platforms (Twitter, Reddit, Discord)
- Redundant information
- Time-consuming reading process

This tool solves these challenges by:
- Automatically fetching the latest RSS feed
- Using Gemini AI to analyze and categorize news by importance
- Generating a clean, structured HTML report
- Eliminating redundancy and highlighting key information

## 🚀 Features

- **Smart Analysis**: Uses Google's Gemini AI to process and understand news context
- **Categorized Output**: Organizes news into:
  - Top News (Major announcements and breakthroughs)
  - High-Level News (Strategic and industry-wide impact)
  - Low-Level News (Technical details and smaller updates)
- **Clean HTML Report**: Generates a well-formatted, easy-to-read report
- **Cross-Platform Analysis**: Consolidates news from Twitter, Reddit, and Discord discussions

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Internet connection for RSS feed access

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/gth-ai/ai_news_rss_summarizer.git
cd ai_news_rss_summarizer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Gemini API key:
   - Create a `config.json` file in the root directory
   - Add your API key in this format:
```json
{
    "google_api_key": "your-api-key-here"
}
```

## 💻 Usage

Run the analyzer:
```bash
python rss_analyzer.py
```

The script will:
1. Fetch the latest AI News RSS feed
2. Process the content using Gemini AI
3. Generate a `news_report.html` file in the current directory
4. Open the report in your default web browser

## 📊 Output Structure

The generated HTML report includes:
- **Executive Summary**: Overview of key trends and patterns
- **Categorized News**:
  - Top News: Critical announcements and breakthroughs
  - High-Level News: Strategic developments and industry trends
  - Low-Level News: Technical updates and community discussions
- **Timestamp**: Generation date and time
- **Source Links**: References to original content

## 🔧 Customization

You can modify the analysis parameters in `rss_analyzer.py`:
- Adjust chunk sizes for analysis
- Modify categorization criteria
- Customize HTML template styling
- Change the RSS feed URL (default: https://buttondown.com/ainews/rss)

## 📝 License

[Your chosen license]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

[Your contact information or preferred method of contact]

---
*Note: This tool is not officially affiliated with AI News or Buttondown.email. It's an independent project designed to enhance the reading experience of their excellent newsletter.* 