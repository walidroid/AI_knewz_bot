import html
import re
import requests
import feedparser

# --- Paramètres Telegram ---
TELEGRAM_BOT_TOKEN = "8904712968:AAHRxkyUQ174_z0CXhH70l3yjH0zp5Dfy1o"
TELEGRAM_CHAT_ID = "1958047631"

# Sources RSS spécialisées IA / Tech
RSS_FEEDS = [
    "https://feeds.feedburner.com/VentureBeat/AI",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab"
]

# Mots-clés pour ne retenir que ce qui touche à l'IA
AI_KEYWORDS = [
    "ai", "llm", "gpt", "model", "deep learning", "machine learning",
    "neural", "agent", "robot", "nvidia", "hugging face", "open-source",
    "intelligence artificielle", "openai", "anthropic", "meta ai"
]

def clean_html(raw_html: str) -> str:
    """Supprime les balises HTML et décode les entités."""
    clean_text = re.sub(r"<[^>]+>", "", raw_html or "")
    return html.unescape(clean_text).strip()

def is_ai_relevant(text: str) -> bool:
    """Filtre basé sur la présence d'au moins un mot-clé."""
    lower = text.lower()
    return any(re.search(rf"\b{kw}\b", lower) for kw in AI_KEYWORDS)

def collect_news(max_items=6):
    seen_titles = set()
    collected = []

    for feed_url in RSS_FEEDS:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            title = clean_html(entry.get("title", ""))
            link = entry.get("link", "")
            summary = clean_html(entry.get("summary", ""))

            # Vérification de pertinence et anti-doublon
            if title and title not in seen_titles:
                if is_ai_relevant(title) or is_ai_relevant(summary):
                    seen_titles.add(title)
                    collected.append({"title": title, "link": link})
                    if len(collected) >= max_items:
                        return collected
    return collected

def send_telegram_digest(articles):
    if not articles:
        print("Aucun article pertinent trouvé.")
        return

    # Construction du message en Markdown Telegram
    lines = ["📰 *Revue de Presse IA (Dernières news)*\n"]
    for i, item in enumerate(articles, start=1):
        # Échappe les crochets pour éviter les erreurs de parsing Markdown
        safe_title = item['title'].replace("[", "(").replace("]", ")")
        lines.append(f"{i}\\. [{safe_title}]({item['link']})")

    message_text = "\n".join(lines)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True  # Évite d'inonder Telegram avec 6 prévisualisations
    }

    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        print("Message envoyé avec succès !")
    else:
        print(f"Erreur Telegram ({res.status_code}) : {res.text}")

if __name__ == "__main__":
    items = collect_news()
    send_telegram_digest(items)
