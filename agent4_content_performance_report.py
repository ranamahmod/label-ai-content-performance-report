"""
Agent 4: Content Performance Report
Generates a weekly HTML performance report using YouTube Data API v3
and LinkedIn API. Includes Chart.js bar/line charts for weekly trends.
Instagram is included as a placeholder (comment in code explains path forward).

Usage:
    python agent4_content_performance_report.py
    (reads all credentials from .env file)
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")  # e.g. urn:li:person:XXXXX
GROQ_MODEL = "llama3-70b-8192"


# ---------------------------------------------------------------------------
# YouTube Data API v3
# ---------------------------------------------------------------------------

def fetch_youtube_channel_stats() -> dict:
    """Fetch channel-level statistics from YouTube Data API v3."""
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
        print("[!] YouTube API key or Channel ID not set. Returning placeholder data.")
        return _youtube_placeholder()

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet",
        "id": YOUTUBE_CHANNEL_ID,
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            print("[!] No YouTube channel found for that ID.")
            return _youtube_placeholder()
        item = items[0]
        stats = item.get("statistics", {})
        return {
            "channel_name": item.get("snippet", {}).get("title", "Your Channel"),
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "total_videos": int(stats.get("videoCount", 0)),
            "status": "live",
        }
    except Exception as e:
        print(f"[!] YouTube channel stats error: {e}")
        return _youtube_placeholder()


def fetch_youtube_top_videos() -> list:
    """Fetch top 5 videos by view count from the channel this week."""
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
        return _youtube_placeholder_videos()

    # Step 1: Search for recent videos
    one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": YOUTUBE_CHANNEL_ID,
        "order": "viewCount",
        "publishedAfter": one_week_ago,
        "maxResults": 10,
        "type": "video",
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(search_url, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]

        if not video_ids:
            return _youtube_placeholder_videos()

        # Step 2: Fetch video statistics
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            "part": "statistics,snippet",
            "id": ",".join(video_ids[:5]),
            "key": YOUTUBE_API_KEY,
        }
        stats_resp = requests.get(stats_url, params=stats_params, timeout=15)
        stats_resp.raise_for_status()
        videos = []
        for v in stats_resp.json().get("items", []):
            stats = v.get("statistics", {})
            snippet = v.get("snippet", {})
            videos.append({
                "title": snippet.get("title", "Unknown")[:60],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "published": snippet.get("publishedAt", "")[:10],
                "url": f"https://www.youtube.com/watch?v={v['id']}",
            })
        return videos or _youtube_placeholder_videos()
    except Exception as e:
        print(f"[!] YouTube videos error: {e}")
        return _youtube_placeholder_videos()


def fetch_youtube_weekly_views() -> dict:
    """
    Fetch daily view data for the past 7 days using YouTube Analytics API.
    Note: Requires OAuth 2.0 (not just API key). This function uses the
    Data API as a proxy by getting recent video stats.
    """
    if not YOUTUBE_API_KEY or not YOUTUBE_CHANNEL_ID:
        return _youtube_placeholder_weekly()

    # The YouTube Analytics API requires OAuth. We approximate weekly data
    # by fetching the last 7 uploaded videos and their stats.
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": YOUTUBE_CHANNEL_ID,
        "order": "date",
        "maxResults": 7,
        "type": "video",
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(search_url, params=params, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        labels = []
        views_data = []
        for item in items[:7]:
            snippet = item.get("snippet", {})
            pub_date = snippet.get("publishedAt", "")[:10]
            labels.append(pub_date)
            # We don't have per-day analytics without OAuth, so use 0 as placeholder
            views_data.append(0)

        if not labels:
            return _youtube_placeholder_weekly()

        return {
            "labels": labels,
            "views": views_data,
            "note": "Daily view counts require YouTube Analytics API (OAuth). Showing upload timeline.",
            "status": "partial",
        }
    except Exception as e:
        print(f"[!] YouTube weekly views error: {e}")
        return _youtube_placeholder_weekly()


def _youtube_placeholder():
    return {
        "channel_name": "Your Channel (configure YOUTUBE_API_KEY + YOUTUBE_CHANNEL_ID)",
        "subscribers": 0,
        "total_views": 0,
        "total_videos": 0,
        "status": "placeholder",
    }


def _youtube_placeholder_videos():
    return [
        {"title": f"Sample Video {i+1} — add YOUTUBE_API_KEY to .env", "views": 0, "likes": 0, "comments": 0, "published": datetime.now().strftime("%Y-%m-%d"), "url": "#"}
        for i in range(3)
    ]


def _youtube_placeholder_weekly():
    past_7 = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    return {
        "labels": past_7,
        "views": [0, 0, 0, 0, 0, 0, 0],
        "note": "Add YOUTUBE_API_KEY and YOUTUBE_CHANNEL_ID to .env",
        "status": "placeholder",
    }


# ---------------------------------------------------------------------------
# LinkedIn API
# ---------------------------------------------------------------------------

def fetch_linkedin_posts() -> list:
    """
    Fetch recent LinkedIn posts for the authenticated user.
    Uses LinkedIn's /ugcPosts endpoint with User Generated Content API.
    Requires: LinkedIn Marketing Developer Program access or basic rw_organization_social.
    """
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
        print("[!] LinkedIn credentials not set. Returning placeholder data.")
        return _linkedin_placeholder_posts()

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Encode the author URN
    author = LINKEDIN_PERSON_URN.replace(":", "%3A")

    url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({author})&sortBy=LAST_MODIFIED&count=10"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("elements", [])
        posts = []
        for item in items[:7]:
            post_id = item.get("id", "")
            content = item.get("specificContent", {})
            share_content = content.get("com.linkedin.ugc.ShareContent", {})
            commentary = share_content.get("shareCommentary", {}).get("text", "")[:200]
            created = item.get("created", {}).get("time", 0)
            created_str = datetime.fromtimestamp(created / 1000).strftime("%Y-%m-%d") if created else "N/A"

            posts.append({
                "id": post_id,
                "commentary": commentary,
                "created": created_str,
                "impressions": 0,  # requires separate analytics call
                "clicks": 0,
                "engagement_rate": "N/A",
            })

        # Attempt to enrich with social metadata
        for post in posts:
            if post["id"]:
                try:
                    social_url = f"https://api.linkedin.com/v2/socialMetadata/{post['id']}"
                    social_resp = requests.get(social_url, headers=headers, timeout=10)
                    if social_resp.ok:
                        social = social_resp.json()
                        post["likes"] = social.get("totalSocialActivityCounts", {}).get("numLikes", 0)
                        post["comments"] = social.get("totalSocialActivityCounts", {}).get("numComments", 0)
                except Exception:
                    pass

        return posts or _linkedin_placeholder_posts()
    except requests.exceptions.HTTPError as e:
        print(f"[!] LinkedIn API HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return _linkedin_placeholder_posts()
    except Exception as e:
        print(f"[!] LinkedIn API error: {e}")
        return _linkedin_placeholder_posts()


def _linkedin_placeholder_posts():
    past_7 = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    return [
        {
            "id": f"placeholder_{i}",
            "commentary": f"Sample LinkedIn post {i+1} — configure LINKEDIN_ACCESS_TOKEN in .env to see real data.",
            "created": past_7[i % 7],
            "impressions": 0,
            "clicks": 0,
            "engagement_rate": "N/A",
            "likes": 0,
            "comments": 0,
        }
        for i in range(5)
    ]


# ---------------------------------------------------------------------------
# AI-powered insights
# ---------------------------------------------------------------------------

def generate_ai_insights(yt_stats: dict, yt_videos: list, linkedin_posts: list) -> str:
    """Use Groq to generate strategic weekly insights."""
    if not GROQ_API_KEY:
        return "Set GROQ_API_KEY in your .env file to enable AI-powered weekly insights."

    client = Groq(api_key=GROQ_API_KEY)

    yt_summary = f"""YouTube Channel: {yt_stats.get('channel_name')}
Subscribers: {yt_stats.get('subscribers', 0):,}
Total Views: {yt_stats.get('total_views', 0):,}
Top videos this week: {', '.join([v['title'] for v in yt_videos[:3]])}"""

    li_summary = f"""LinkedIn posts this week: {len(linkedin_posts)}
Sample posts: {' | '.join([p['commentary'][:100] for p in linkedin_posts[:3]])}"""

    prompt = f"""You are a content performance strategist reviewing weekly analytics.

WEEKLY DATA SUMMARY:

{yt_summary}

{li_summary}

Provide 3-4 bullet-point strategic insights for next week's content plan. Be specific and actionable.
Format: Start each bullet with "• " and keep it under 2 sentences per bullet.
No markdown headers, just the bullets."""

    try:
        chat = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        return f"AI insight generation failed: {e}"


# ---------------------------------------------------------------------------
# HTML Report Builder
# ---------------------------------------------------------------------------

def build_html_report(
    yt_stats: dict,
    yt_videos: list,
    yt_weekly: dict,
    linkedin_posts: list,
    ai_insights: str,
    report_date: str,
) -> str:
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    week_start = (datetime.now() - timedelta(days=6)).strftime("%b %d")
    week_end = datetime.now().strftime("%b %d, %Y")

    # YouTube top videos table rows
    yt_rows = ""
    for v in yt_videos:
        yt_rows += f"""
        <tr>
          <td><a href="{v.get('url', '#')}" target="_blank" style="color:#a5b4fc;">{v.get('title', 'N/A')}</a></td>
          <td>{v.get('views', 0):,}</td>
          <td>{v.get('likes', 0):,}</td>
          <td>{v.get('comments', 0):,}</td>
          <td>{v.get('published', 'N/A')}</td>
        </tr>"""

    # LinkedIn posts table rows
    li_rows = ""
    for p in linkedin_posts:
        li_rows += f"""
        <tr>
          <td style="max-width:320px;">{p.get('commentary', 'N/A')}</td>
          <td>{p.get('impressions', 0):,}</td>
          <td>{p.get('likes', 0):,}</td>
          <td>{p.get('comments', 0):,}</td>
          <td>{p.get('created', 'N/A')}</td>
        </tr>"""

    # Charts data
    yt_labels = json.dumps(yt_weekly.get("labels", []))
    yt_views = json.dumps(yt_weekly.get("views", []))
    weekly_note = yt_weekly.get("note", "")

    li_labels = json.dumps([p.get("created", "") for p in linkedin_posts])
    li_impressions = json.dumps([p.get("impressions", 0) for p in linkedin_posts])

    ai_bullets_html = "".join(
        f"<li>{line.lstrip('•').strip()}</li>"
        for line in ai_insights.split("\n")
        if line.strip()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Content Performance Report — {report_date}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117; --card: #1a1d27; --accent: #6c63ff;
    --yt: #ff0000; --li: #0077b5; --accent3: #43e97b;
    --text: #e2e8f0; --muted: #94a3b8; --border: #2d3148;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; }}
  .header {{ background: linear-gradient(135deg, #1a1d27 0%, #1a0a0a 100%); border-bottom: 2px solid var(--yt); padding: 36px 48px; }}
  .header h1 {{ font-size: 2rem; font-weight: 700; color: #fff; }}
  .header .subtitle {{ color: var(--muted); margin-top: 8px; }}
  .header .period {{ color: var(--accent3); font-size: 0.9rem; margin-top: 8px; font-weight: 600; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px; }}
  .platform-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}
  .platform-logo {{ font-size: 1.4rem; }}
  .platform-title {{ font-size: 1.2rem; font-weight: 700; color: #fff; }}
  .platform-badge {{ display: inline-block; padding: 3px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .badge-yt {{ background: #3b0000; color: #fca5a5; border: 1px solid var(--yt); }}
  .badge-li {{ background: #001a2d; color: #93c5fd; border: 1px solid var(--li); }}
  .stats-row {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 24px; flex: 1; min-width: 130px; }}
  .stat-val {{ font-size: 1.5rem; font-weight: 700; color: #fff; }}
  .stat-label {{ color: var(--muted); font-size: 0.75rem; margin-top: 4px; text-transform: uppercase; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 28px; margin-bottom: 24px; }}
  .section-title {{ font-size: 1rem; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 16px; }}
  .chart-wrap {{ position: relative; height: 220px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; }}
  td {{ padding: 12px 12px; border-bottom: 1px solid #1e2333; color: var(--text); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #1e2333; }}
  .divider {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
  .ai-list {{ list-style: none; }}
  .ai-list li {{ padding: 12px 0; border-bottom: 1px solid var(--border); color: var(--text); font-size: 0.92rem; line-height: 1.6; }}
  .ai-list li::before {{ content: "→ "; color: var(--accent3); font-weight: 700; }}
  .ai-list li:last-child {{ border-bottom: none; }}
  .weekly-note {{ color: var(--muted); font-size: 0.8rem; font-style: italic; margin-top: 8px; }}
  .ig-placeholder {{ background: #1a1a2e; border: 1px dashed #4c4c7a; border-radius: 10px; padding: 20px; color: var(--muted); font-size: 0.88rem; line-height: 1.6; }}
  .footer {{ text-align: center; padding: 32px; color: var(--muted); font-size: 0.82rem; border-top: 1px solid var(--border); margin-top: 20px; }}
</style>
</head>
<body>
<div class="header">
  <h1>Content Performance Report</h1>
  <div class="subtitle">Weekly analytics across YouTube, LinkedIn, and Instagram</div>
  <div class="period">Week of {week_start} — {week_end}</div>
</div>

<div class="container">

  <!-- YouTube Section -->
  <div class="platform-header">
    <div class="platform-logo">▶️</div>
    <div class="platform-title">YouTube</div>
    <span class="platform-badge badge-yt">YouTube Data API v3</span>
  </div>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-val">{yt_stats.get('subscribers', 0):,}</div>
      <div class="stat-label">Subscribers</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{yt_stats.get('total_views', 0):,}</div>
      <div class="stat-label">Total Views</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">{yt_stats.get('total_videos', 0):,}</div>
      <div class="stat-label">Total Videos</div>
    </div>
    <div class="stat-card" style="flex:2;">
      <div class="stat-val" style="font-size:1rem;">{yt_stats.get('channel_name', 'N/A')}</div>
      <div class="stat-label">Channel</div>
    </div>
  </div>

  <div class="card">
    <div class="section-title">Weekly Upload Timeline</div>
    <div class="chart-wrap"><canvas id="ytChart"></canvas></div>
    <div class="weekly-note">{weekly_note}</div>
  </div>

  <div class="card">
    <div class="section-title">Top Videos This Week</div>
    <table>
      <thead><tr><th>Title</th><th>Views</th><th>Likes</th><th>Comments</th><th>Published</th></tr></thead>
      <tbody>{yt_rows}</tbody>
    </table>
  </div>

  <hr class="divider"/>

  <!-- LinkedIn Section -->
  <div class="platform-header">
    <div class="platform-logo">💼</div>
    <div class="platform-title">LinkedIn</div>
    <span class="platform-badge badge-li">LinkedIn API</span>
  </div>

  <div class="card">
    <div class="section-title">Weekly Post Performance</div>
    <div class="chart-wrap"><canvas id="liChart"></canvas></div>
  </div>

  <div class="card">
    <div class="section-title">Recent Posts</div>
    <table>
      <thead><tr><th>Post</th><th>Impressions</th><th>Likes</th><th>Comments</th><th>Date</th></tr></thead>
      <tbody>{li_rows}</tbody>
    </table>
  </div>

  <hr class="divider"/>

  <!-- Instagram Placeholder -->
  <div class="platform-header">
    <div class="platform-logo">📸</div>
    <div class="platform-title">Instagram</div>
  </div>
  <div class="ig-placeholder">
    <strong>Instagram Business / Creator API</strong> requires Facebook Business Manager approval and the
    <em>instagram_basic</em> + <em>instagram_manage_insights</em> permissions via a connected Facebook Page.<br/><br/>
    To enable Instagram analytics: register your app at
    <a href="https://developers.facebook.com/apps/" style="color:#a5b4fc;" target="_blank">developers.facebook.com</a>,
    connect your Instagram Business account, obtain a long-lived Page Access Token, and call
    <code>/me/media?fields=id,caption,media_type,timestamp,like_count,comments_count,insights</code>.
    Add <code>INSTAGRAM_ACCESS_TOKEN</code> and <code>INSTAGRAM_PAGE_ID</code> to your .env file,
    then extend this agent with a <code>fetch_instagram_posts()</code> function following the same pattern as LinkedIn above.
  </div>

  <hr class="divider"/>

  <!-- AI Insights -->
  <div class="card">
    <div class="section-title">AI-Powered Weekly Insights</div>
    <ul class="ai-list">{ai_bullets_html}</ul>
  </div>

</div>

<div class="footer">
  Generated by The Label AI Studios PH — Content Performance Report Agent &nbsp;|&nbsp; Powered by Groq AI + llama3-70b-8192<br/>
  Report Date: {timestamp}
</div>

<script>
new Chart(document.getElementById('ytChart'), {{
  type: 'bar',
  data: {{
    labels: {yt_labels},
    datasets: [{{
      label: 'Views / Upload Activity',
      data: {yt_views},
      backgroundColor: 'rgba(255,0,0,0.6)',
      borderColor: '#ff0000',
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#e2e8f0' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#2d3148' }} }},
      y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#2d3148' }}, beginAtZero: true }}
    }}
  }}
}});

new Chart(document.getElementById('liChart'), {{
  type: 'line',
  data: {{
    labels: {li_labels},
    datasets: [{{
      label: 'Impressions',
      data: {li_impressions},
      borderColor: '#0077b5',
      backgroundColor: 'rgba(0,119,181,0.15)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#0077b5',
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#e2e8f0' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#2d3148' }} }},
      y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#2d3148' }}, beginAtZero: true }}
    }}
  }}
}});
</script>
</body>
</html>"""
    return html


def main():
    report_date = datetime.now().strftime("%Y-%m-%d")
    print(f"[*] Generating Content Performance Report for week ending {report_date}")

    print("[*] Fetching YouTube channel stats...")
    yt_stats = fetch_youtube_channel_stats()

    print("[*] Fetching YouTube top videos...")
    yt_videos = fetch_youtube_top_videos()

    print("[*] Fetching YouTube weekly data...")
    yt_weekly = fetch_youtube_weekly_views()

    print("[*] Fetching LinkedIn posts...")
    linkedin_posts = fetch_linkedin_posts()

    print("[*] Generating AI insights...")
    ai_insights = generate_ai_insights(yt_stats, yt_videos, linkedin_posts)

    html = build_html_report(yt_stats, yt_videos, yt_weekly, linkedin_posts, ai_insights, report_date)

    output_file = f"performance_report_{report_date}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[✓] Performance report saved: {output_file}")
    print(f"    YouTube: {yt_stats.get('channel_name')} | {yt_stats.get('subscribers', 0):,} subscribers")
    print(f"    LinkedIn: {len(linkedin_posts)} posts retrieved")


if __name__ == "__main__":
    main()
