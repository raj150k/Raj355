#!/usr/bin/env python3
import os, sys, subprocess, logging

# ── Auto install FFmpeg if missing (fix for Render free tier) ──
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
except:
    print("Installing FFmpeg...")
    subprocess.run(["apt-get", "update", "-qq"], check=False)
    subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=True)
    print("FFmpeg installed!")

from flask import Flask, request
from telegram import Update
from config import config
from bot import build_app

flask_app = Flask(__name__)
application = None

@flask_app.route("/")
def home():
    return "Bot Running! Add /healthz for uptime monitor.", 200

@flask_app.route(f"/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    global application
    if application:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
    return "OK", 200

@flask_app.route("/healthz")
def health():
    return "alive", 200

def main():
    global application
    logging.basicConfig(level=logging.WARNING)
    application = build_app()
    port = int(os.getenv("PORT", 10000))
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        print("RENDER_EXTERNAL_URL not set!")
        sys.exit(1)
    wh = f"{url}/{config.BOT_TOKEN}"
    print(f"Setting webhook: {wh}")
    application.bot.set_webhook(url=wh)
    print(f"Bot running on port {port}")
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
