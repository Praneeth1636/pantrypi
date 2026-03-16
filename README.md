# PantryPi

A self-hosted recipe manager and grocery planner that runs on a Raspberry Pi. No cloud accounts, no subscriptions, no tracking. Your recipes live on your network, accessible from any device with a browser.

Built with Flask, SQLite, and plain HTML/CSS. The entire app is a single Python process with a ~10KB stylesheet — light enough to run on a Pi Zero.

## Why

Every recipe app wants you to create an account, watch ads, or pay $8/month to save a grocery list. PantryPi runs on hardware you already own, stores data in a single SQLite file, and works from your phone in the kitchen without an internet connection.

## What It Does

**Working now:**
- Add, edit, and delete recipes with ingredients, tags, prep/cook times, and step-by-step instructions
- Search recipes by name, description, or ingredient ("what can I make with chicken?")
- Tag recipes and browse by tag
- Dynamic ingredient editor — add rows on the fly without page reloads

**In progress:**
- Weekly meal planner (assign recipes to breakfast/lunch/dinner slots)
- Auto-generated grocery lists from your meal plan
- Photo uploads with automatic WebP compression
- Raspberry Pi deployment configs (Nginx, systemd)

## Screenshots

*Coming once the planner and grocery features land. For now, clone it and run locally — it takes 30 seconds.*

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Flask (Python) | Minimal, no magic, easy to deploy on a Pi |
| Database | SQLite | Single file, zero config, backs up with `cp` |
| Frontend | Vanilla HTML/CSS/JS | No build step, no node_modules, loads instantly |
| Templating | Jinja2 (server-side) | Pages work without JavaScript |
| Production | Gunicorn + Nginx | Nginx serves static files, Gunicorn runs the app |

No React. No Tailwind. No Docker. This runs on a $15 computer.

## Quick Start (Local Development)

```bash
git clone https://github.com/Praneeth1636/pantrypi.git
cd pantrypi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5001](http://localhost:5001). The database is created automatically on the first request.

## Raspberry Pi Setup

> Full deployment guide coming soon. Short version:

1. Flash **Raspberry Pi OS Lite** to an SD card, enable SSH
2. SSH in, clone this repo to `~/pantrypi`
3. Create a virtualenv, install requirements
4. Run with Gunicorn: `gunicorn -w 2 -b 127.0.0.1:8000 "app:create_app()"`
5. Put Nginx in front to serve static files and proxy to Gunicorn
6. Set up a systemd service so it starts on boot

Access from any device on your network at `http://<pi-ip-address>`.

## Project Structure

```
pantrypi/
├── app.py                 # App factory, DB helpers, custom Jinja filters
├── schema.sql             # SQLite schema (6 tables)
├── requirements.txt       # Flask, Gunicorn, Pillow, requests, beautifulsoup4
├── routes/
│   ├── recipes.py         # Recipe CRUD + search (fully implemented)
│   ├── planner.py         # Meal planner (in progress)
│   └── grocery.py         # Grocery list (in progress)
├── templates/
│   ├── base.html          # Layout shell with sticky nav
│   ├── index.html          # Home page
│   └── recipes/
│       ├── _recipe_grid.html  # Reusable recipe card grid partial
│       ├── list.html          # Recipe browser
│       ├── detail.html        # Single recipe view
│       └── edit.html          # Create/edit form
└── static/
    ├── style.css           # All styles, single file (~6KB)
    └── app.js              # Minimal JS for dynamic ingredient rows
```

## Design Decisions

**Server-side rendering, not a SPA.** Every page works without JavaScript. The only JS is for progressive enhancement (adding ingredient rows dynamically). This means the app works on old phones, slow connections, and browsers with JS disabled.

**One CSS file, no framework.** The stylesheet uses CSS custom properties for theming, CSS Grid for layout, and system fonts. No utility classes, no preprocessor, no build step.

**SQLite, not Postgres.** For a single-household app, SQLite is the right tool. The database is a single file you can back up with `cp pantrypi.db pantrypi.db.bak`. Foreign keys are enforced per-connection via `PRAGMA foreign_keys = ON`.

## Contributing

This is a personal project, but if you want to contribute:

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/meal-planner`)
3. Make your changes, keep commits focused
4. Open a PR with a clear description of what changed and why

Please keep the stack minimal. If a feature can be done without adding a dependency, do it without adding a dependency.

## License

MIT
