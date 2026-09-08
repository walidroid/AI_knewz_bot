import html
import os
import re
import requests
import feedparser

# Load credentials securely from environment variables (GitHub Secrets or local env)
# Fallback to defaults only for local testing if needed
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RSS_FEEDS = [
    "https://feeds.feedburner.com/VentureBeat/AI",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab"
]

AI_KEYWORDS = [
    "ai", "llm", "gpt", "model", "deep learning", "machine learning",
    "neural", "agent", "robot", "nvidia", "hugging face", "open-source",
    "intelligence artificielle", "openai", "anthropic", "meta ai"
]

def clean_html(raw_html: str) -> str:
    """Strip HTML tags and unescape characters."""
    clean_text = re.sub(r"<[^>]+>", "", raw_html or "")
    return html.unescape(clean_text).strip()

def is_ai_relevant(text: str) -> bool:
    """Check if any keyword matches."""
    lower = text.lower()
    return any(re.search(rf"\b{kw}\b", lower) for kw in AI_KEYWORDS)

def collect_news(max_items=6):
    seen_titles = set()
    collected = []

    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                title = clean_html(entry.get("title", ""))
                link = entry.get("link", "")
                summary = clean_html(entry.get("summary", ""))

                if title and title not in seen_titles:
                    if is_ai_relevant(title) or is_ai_relevant(summary):
                        seen_titles.add(title)
                        collected.append({"title": title, "link": link})
                        if len(collected) >= max_items:
                            return collected
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            
    return collected

def send_telegram_digest(articles):
    if not articles:
        print("No relevant articles found.")
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing!")
        return

    # Using HTML parse_mode avoids MarkdownV2 character escaping crashes
    lines = ["<b>📰 Revue de Presse IA (Dernières news)</b>\n"]
    for i, item in enumerate(articles, start=1):
        safe_title = html.escape(item['title'])
        safe_link = item['link']
        lines.append(f"{i}. <a href=\"{safe_link}\">{safe_title}</a>")

    message_text = "\n".join(lines)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print("Message delivered successfully to Telegram!")
        else:
            print(f"Telegram API Error ({res.status_code}): {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"Network request failed: {e}")

if __name__ == "__main__":
    items = collect_news()
    send_telegram_digest(items)
