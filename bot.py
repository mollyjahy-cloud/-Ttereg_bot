import os
import re
import logging
from collections import Counter

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Common English stopwords filtered out of hashtag candidates
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "up", "about", "into", "over", "after", "as", "it", "this",
    "that", "these", "those", "i", "you", "he", "she", "we", "they", "my",
    "your", "his", "her", "our", "their", "not", "no", "yes", "so", "if",
    "than", "then", "just", "very", "can", "will", "would", "should",
    "could", "do", "does", "did", "have", "has", "had", "am", "im", "its",
    "me", "us", "them", "there", "here", "what", "when", "where", "why",
    "how", "all", "any", "some", "more", "most", "other", "such", "own",
    "same", "too", "s", "t", "d", "ll", "re", "ve",
}

MAX_HASHTAGS = 15
MAX_WORD_LEN = 30


def generate_hashtags(text: str, limit: int = 10):
    """Extract candidate keywords from text and turn them into hashtags."""
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    words = [w.strip("'") for w in words]

    candidates = [
        w for w in words
        if w
        and w not in STOPWORDS
        and len(w) > 2
        and len(w) <= MAX_WORD_LEN
        and not w.isdigit()
    ]

    if not candidates:
        return []

    counts = Counter(candidates)
    seen_order = []
    seen_set = set()
    for w in candidates:
        if w not in seen_set:
            seen_set.add(w)
            seen_order.append(w)

    ranked = sorted(seen_order, key=lambda w: (-counts[w], seen_order.index(w)))
    top = ranked[:limit]

    return ["#" + w for w in top]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm HashtagGenBot.\n\n"
        "Send me any text, caption, or topic and I'll generate relevant "
        "hashtags for it.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - How to use this bot\n\n"
        "Just type or paste your text to get started!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 How to use HashtagGenBot:\n\n"
        "1. Send any message, caption, or short paragraph.\n"
        "2. I'll extract the key words and turn them into hashtags.\n"
        "3. Copy and paste the hashtags into your post.\n\n"
        f"I generate up to {MAX_HASHTAGS} hashtags per message."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if not text.strip():
        await update.message.reply_text("Please send some text to generate hashtags from.")
        return

    hashtags = generate_hashtags(text, limit=MAX_HASHTAGS)

    if not hashtags:
        await update.message.reply_text(
            "I couldn't find enough meaningful words in that text. "
            "Try sending a longer sentence or a few keywords."
        )
        return

    await update.message.reply_text(" ".join(hashtags))


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it in Railway's Variables tab or your local .env file."
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("HashtagGenBot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
