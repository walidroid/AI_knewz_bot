import html
import os
import re
import requests
import feedparser

# Load credentials from environment variables (GitHub Secrets or local env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://news.ycombinator.com/rss",  # Hacker News Top Stories
    "https://feeds.feedburner.com/VentureBeat/AI",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab"
]

AI_KEYWORDS = [
    "ai", "llm", "gpt", "model", "deep learning", "machine learning",
    "neural", "agent", "robot", "nvidia", "hugging face", "open-source",
    "intelligence artificielle", "openai", "anthropic", "meta", "google",
    "gemini", "claude", "mistral", "chip", "tech"
]

def clean_html(raw_html: str) -> str:
    """Strip HTML tags and unescape characters."""
    clean_text = re.sub(r"<[^>]+>", "", raw_html or "")
    return html.unescape(clean_text).strip()

def is_ai_relevant(text: str) -> bool:
    """Check if any AI/Tech keyword matches."""
    lower = text.lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", lower) for kw in AI_KEYWORDS)

def collect_news(max_items=10):
    seen_titles = set()
    collected = []
    fallback_articles = []

    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching feed: {feed_url}")
            parsed = feedparser.parse(feed_url, agent="Mozilla/5.0 (NewsBot/1.0)")
            for entry in parsed.entries:
                title = clean_html(entry.get("title", ""))
                link = entry.get("link", "")
                summary = clean_html(entry.get("summary", ""))

                if title and title not in seen_titles:
                    seen_titles.add(title)
                    item = {"title": title, "link": link}
                    
                    if is_ai_relevant(title) or is_ai_relevant(summary):
                        collected.append(item)
                    else:
                        fallback_articles.append(item)

                    if len(collected) >= max_items:
                        return collected
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")

    # Fallback to general tech articles if strict keyword matches are under target
    if len(collected) < max_items:
        needed = max_items - len(collected)
        collected.extend(fallback_articles[:needed])

    return collected

def send_telegram_digest(articles):
    print(f"DEBUG: Found {len(articles)} articles.")
    print(f"DEBUG: TELEGRAM_BOT_TOKEN present? {bool(TELEGRAM_BOT_TOKEN)}")
    print(f"DEBUG: TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing from environment variables!")

    if not articles:
        print("No articles to send.")
        return

    # Header with bold typography
    lines = [
        "⚡ <b>VEILLE TECH &amp; IA</b> ⚡",
        
    ]

    for i, item in enumerate(articles, start=1):
        safe_title = html.escape(item['title'])
        safe_link = item['link']
        
        # Extract the source domain name for the monospace badge
        try:
            domain = safe_link.split('/')[2].replace('www.', '').replace('feeds.', '')
        except Exception:
            domain = "web"

        # Telegram card layout using blockquote and code tags
        card = (
            f"<blockquote>"
            f"{i}. <b><a href=\"{safe_link}\">{safe_title}</a></b>\n"
            f"🏷️ <code>{domain}</code>"
            f"</blockquote>"
        )
        lines.append(card)

    message_text = "\n".join(lines)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload, timeout=15)
    print(f"Telegram API Status: {response.status_code}")
    print(f"Telegram API Response: {response.text}")

    if response.status_code != 200:
        raise RuntimeError(f"Telegram error {response.status_code}: {response.text}")
    else:
        print("Message sent successfully!")

if __name__ == "__main__":
    # Adjust max_items here if you want more or fewer articles
    items = collect_news(max_items=10)
    send_telegram_digest(items)
