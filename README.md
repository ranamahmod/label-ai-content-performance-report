# label-ai-content-performance-report

An AI agent that connects LinkedIn and YouTube and auto-generates a weekly HTML performance report with graphs and AI-powered callouts.

## What It Does

Run the agent once a week (or schedule it via cron). It pulls YouTube channel statistics and top video data via the YouTube Data API v3, fetches recent LinkedIn posts via the LinkedIn UGC Posts API, then passes the combined data to Groq AI to generate 3–4 strategic insights for the coming week. The output is a dark-themed HTML report with bar charts, line charts, data tables, and an Instagram placeholder section with setup instructions.

## Who Buys This and at What Price

Content creators, personal brands, coaches, and marketing agencies who manage YouTube and LinkedIn channels and want an automated weekly performance snapshot without logging into multiple dashboards. Priced as a weekly automated report service at $200–$500/month per client, or as a one-time setup at $500–$1,000.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in all required keys
```

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key from [console.groq.com](https://console.groq.com) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com) |
| `YOUTUBE_CHANNEL_ID` | Your YouTube channel ID (found in YouTube Studio > Settings > Channel) |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth 2.0 access token with `r_liteprofile` and `r_ugcpost` scopes |
| `LINKEDIN_PERSON_URN` | Your LinkedIn person URN, e.g. `urn:li:person:XXXXXXX` |

Add these to your `.env` file. The agent runs fully from environment variables — no CLI arguments needed.

## Usage

```bash
python agent4_content_performance_report.py
```

No arguments required. All configuration is read from `.env`.

## Output

A timestamped HTML report is saved in the current directory:

```
performance_report_2026-06-01.html
```

The report includes:
- YouTube: subscriber count, total views, total videos, weekly upload timeline chart, top 5 videos table
- LinkedIn: impressions line chart, recent posts table with likes and comments
- Instagram: setup instructions for adding Instagram Business API (ready-to-extend placeholder)
- AI-powered weekly insights: 3–4 strategic bullets for next week's content plan

## Notes

YouTube daily view analytics require the YouTube Analytics API with OAuth 2.0. The agent uses the Data API as an approximation, showing upload activity rather than per-day view counts. LinkedIn's UGC Posts API requires your app to be approved for the Marketing Developer Program for full impression data; basic post retrieval works with standard OAuth scopes.

---

Built by Rana Mahmod (Contact: mahmodrana24@gmail.com)
