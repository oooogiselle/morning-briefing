#!/usr/bin/env python3
"""
Giselle's Morning Briefing Scheduler
Runs daily at 7:00 AM ET, compiles news via Claude API, sends to Gmail.
Render-ready: includes a Flask health endpoint so the free web service stays alive.
"""

import os
import re
import smtplib
import logging
import threading
import time
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
import schedule
from flask import Flask

# ─── CONFIG ───────────────────────────────────────────────────────────────────
# On Render, set these as Environment Variables (never hardcode secrets).
# Locally, you can paste them directly here for testing.
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
GMAIL_SENDER       = os.environ["GMAIL_SENDER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL    = os.environ["RECIPIENT_EMAIL"]
SEND_TIME          = os.environ.get("SEND_TIME", "12:00")  # UTC — 12:00 UTC = 8:00 AM ET
PORT               = int(os.environ.get("PORT", 8080))
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

NATAL_SUMMARY = """Giselle's real natal chart (Swiss Ephemeris, Jan 7 2005, 1:58pm Shanghai, Placidus):
Sun: Capricorn 17° | Moon: Sagittarius 1° | Mercury: Sagittarius 26° | Venus: Sagittarius 26°
Mars: Sagittarius 8° | Jupiter: Libra 17° | Saturn: Cancer 24° | Uranus: Pisces 4°
Neptune: Aquarius 14° | Pluto: Sagittarius 22° | Rising (ASC): Gemini 3° | MC: Aquarius 15° | North Node: Aries 27°
Key themes: Massive Sagittarius stellium — wired for bold exploration, big thinking, going international.
Gemini rising = curious, communicative. Aquarius MC = career in tech/innovation is in the chart.
North Node Aries = destiny is in leadership and pioneering."""

def build_system_prompt():
    today = date.today().strftime("%A, %B %d, %Y")
    return f"""You are compiling Giselle's Morning Briefing — a deep daily digest for Giselle, a third-year CS + Computer Engineering student at Dartmouth (graduating 2027, GPA 3.85). She is job-hunting for software/AI engineering roles.

TODAY: {today}

LENS: After every story (except Celebrity Drama and Astrology), append on its own line:
→ Why it matters for you: [one blunt, specific sentence about job market signal, skill to study, or industry direction by 2027]

Search the web for today's actual news. Compile with EXACTLY these sections:

## ◈ AI & Tech
4–6 stories. LLM releases, GPU/chip news, dev tools, AI systems, CS research.
**Bold headline**
2–3 sentence summary. (Source)
→ Why it matters for you: sentence

## △ Markets & Finance
4–5 stories. Exact S&P/NASDAQ/Dow numbers. Tech stock moves. Macro.
**Bold headline**
Summary with numbers. (Source)
→ Why it matters for you: sentence

## ○ International
4–5 stories. Geopolitics, conflicts, diplomacy.
**Bold headline**
Summary. (Source)
→ Why it matters for you: sentence

## ◆ China Focus
3–4 stories. Chinese tech, policy, US-China, Chinese AI.
**Bold headline**
Summary. (Source)
→ Why it matters for you: sentence

## ◉ Startups & VC
3–4 stories. Funding rounds, acquisitions, hot launches, VC trends.
**Bold headline**
Summary. (Source)
→ Why it matters for you: sentence

## ◇ Exec Pulse
3–4 items from: Elon Musk, Sam Altman, Mark Zuckerberg, Tim Cook, Andy Jassy, Sundar Pichai, Jensen Huang, Dario Amodei, Satya Nadella, Andrej Karpathy, Marc Andreessen.
**[Person] — headline**
Summary. (Source)
→ Why it matters for you: sentence

## ✦ Drama
2–3 items. Brief. No lens needed.

## ♑ Your Chart
Write Giselle a real daily horoscope using her ACTUAL natal chart and today's planetary transits.
Reference real placements by name. Grounded, career-focused, personal. 5–6 sentences flowing paragraph.

{NATAL_SUMMARY}"""


def compile_briefing() -> str:
    today = date.today().strftime("%A, %B %d, %Y")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logging.info("Compiling briefing via Claude API...")
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4500,
        system=build_system_prompt(),
        messages=[{
            "role": "user",
            "content": (
                f"Compile today's full morning briefing. Today is {today}. "
                "Search the web for the latest across all sections. "
                "Specific numbers, names, and dates throughout."
            )
        }],
        tools=[{"type": "web_search_20250305", "name": "web_search"}]
    )
    text = " ".join(
        block.text for block in response.content if hasattr(block, "text")
    )
    logging.info(f"Briefing compiled — {len(text)} chars.")
    return text


def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    html = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            html.append(
                f'<h2 style="font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;'
                f'color:#888;border-top:1px solid #eee;padding-top:24px;margin:32px 0 12px">'
                f'{line[3:]}</h2>'
            )
        elif line.startswith("**") and line.endswith("**"):
            html.append(
                f'<p style="font-weight:600;font-size:15px;color:#111;margin:16px 0 4px;letter-spacing:-.01em">'
                f'{line[2:-2]}</p>'
            )
        elif line.startswith("→ Why it matters for you:"):
            rest = line[len("→ Why it matters for you:"):].strip()
            html.append(
                f'<div style="display:flex;gap:8px;margin:6px 0 16px;padding:8px 12px;'
                f'background:#f5f8ff;border-radius:6px;border-left:2px solid #4f7cff">'
                f'<span style="font-size:10px;font-family:monospace;color:#4f7cff;margin-top:2px;flex-shrink:0;letter-spacing:.06em">YOU</span>'
                f'<span style="font-size:13px;color:#444;line-height:1.55">{rest}</span></div>'
            )
        else:
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            html.append(
                f'<p style="font-size:14px;color:#555;line-height:1.75;margin:3px 0 6px">{formatted}</p>'
            )
    return "\n".join(html)


def send_email(briefing_text: str) -> None:
    today = date.today().strftime("%A, %B %d, %Y")
    subject = f"☀️ Giselle's Morning Briefing — {today}"
    body_html = f"""
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    max-width:660px;margin:0 auto;padding:40px 28px;color:#111;background:#fff">
  <div style="border-bottom:1px solid #eee;padding-bottom:24px;margin-bottom:4px">
    <p style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#aaa;
       margin:0 0 12px;font-family:monospace">{today}</p>
    <h1 style="font-size:30px;font-weight:400;margin:0;letter-spacing:-1px;line-height:1.1;
       font-family:Georgia,serif">Giselle's<br/>Morning Briefing</h1>
  </div>
  {markdown_to_html(briefing_text)}
  <div style="border-top:1px solid #eee;margin-top:48px;padding-top:16px">
    <p style="font-size:10px;color:#ccc;margin:0;font-family:monospace;letter-spacing:.06em">
      COMPILED BY CLAUDE · CAPRICORN EDITION · {today.upper()}
    </p>
  </div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(briefing_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    logging.info("Sending via Gmail SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, RECIPIENT_EMAIL, msg.as_string())
    logging.info(f"Sent to {RECIPIENT_EMAIL}")


def run_briefing():
    logging.info("=== Morning briefing pipeline starting ===")
    try:
        briefing = compile_briefing()
        send_email(briefing)
        logging.info("=== Pipeline complete ===")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")


def run_scheduler():
    logging.info(f"Scheduler started — will fire daily at {SEND_TIME} UTC")
    schedule.every().day.at(SEND_TIME).do(run_briefing)
    # Uncomment to test immediately on first deploy:
    # run_briefing()
    while True:
        schedule.run_pending()
        time.sleep(30)


# ─── Flask health server (required by Render free tier) ──────────────────────
app = Flask(__name__)

@app.route("/")
def index():
    return f"Giselle's Morning Briefing — running. Next send: {SEND_TIME} UTC daily.", 200

@app.route("/health")
def health():
    return "ok", 200

@app.route("/send-now")
def send_now():
    """Manual trigger — hit this URL to fire a briefing immediately."""
    thread = threading.Thread(target=run_briefing)
    thread.start()
    return "Briefing compiling — check your inbox in ~60s.", 200


if __name__ == "__main__":
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    # Start Flask in main thread (Render binds to PORT env var)
    app.run(host="0.0.0.0", port=PORT)