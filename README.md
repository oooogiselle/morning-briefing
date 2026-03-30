# ☀️ Giselle's Morning Briefing

A personal daily news digest compiled by Claude, delivered to my inbox every morning at 8 AM ET.

## What it does

Searches the web across 14+ sources, compiles a deep briefing across 8 sections, and emails it automatically via GitHub Actions — completely free.

### Sections
- **◈ AI & Tech** — LLM releases, GPU/chip news, dev tools, CS research
- **△ Markets & Finance** — S&P, NASDAQ, Dow, tech stocks
- **○ International** — Geopolitics, conflicts, diplomacy
- **◆ China Focus** — Chinese tech, policy, US-China relations
- **◉ Startups & VC** — Funding rounds, acquisitions, hot launches
- **◇ Exec Pulse** — Posts & news from top tech CEOs
- **✦ Drama** — Celebrity news
- **♑ Your Chart** — Daily horoscope based on my real natal chart (Swiss Ephemeris)

Every story includes a **"Why it matters for you"** lens — filtered for a CS/CE student job-hunting for AI/software engineering roles graduating 2027.

## Sources

AI Valley · Exec Sum · TLDR AI · New York Times · Hacker News · Substack · The Guardian · BBC · 人民日报 · South China Morning Post · MIT Tech Review · The Information · Bloomberg Tech · ArXiv CS/AI

## How it works

```
GitHub Actions (cron: 8 AM ET)
    → briefing_scheduler.py
        → Claude API (web search enabled)
        → Gmail SMTP
            → inbox
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/oooogiselle/morning-briefing
cd morning-briefing
```

### 2. Add GitHub secrets
Go to repo → Settings → Secrets and variables → Actions → add:

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | From console.anthropic.com |
| `GMAIL_SENDER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | 16-char app password from myaccount.google.com/apppasswords |
| `RECIPIENT_EMAIL` | Where to send the briefing |

### 3. Run manually
Go to Actions → Morning Briefing → Run workflow

It runs automatically every day at 12:00 UTC (8:00 AM ET).

## Local setup

```bash
pip install anthropic schedule flask

export ANTHROPIC_API_KEY=your_key
export GMAIL_SENDER=you@gmail.com
export GMAIL_APP_PASSWORD=your_app_password
export RECIPIENT_EMAIL=you@gmail.com

python3 briefing_scheduler.py
```

## Astrology

The horoscope section uses a real natal chart calculated via Swiss Ephemeris:
- **Sun** Capricorn 17° · **Moon** Sagittarius 1° · **Rising** Gemini 3° · **MC** Aquarius 15°
- Sagittarius stellium (Moon, Mars, Mercury, Venus, Pluto)
- North Node Aries 27°

Daily readings are based on actual planetary transits hitting natal placements — not generic sun sign content.