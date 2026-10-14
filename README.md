# Fraud Apps Finalcode Faraz Noor

FraudApps-finalcode-Faraz-Noor is an application for analysing app reviews and potentially fraudulent apps.

![Flask](https://img.shields.io/badge/Flask-2563EB?style=flat-square) ![SQLite](https://img.shields.io/badge/SQLite-0F172A?style=flat-square)

## Overview

The Flask implementation is organized around the entry points and modules below.

## Implemented workflows

The source defines these handlers:

- **Home** — `home`
- **Register** — `register`
- **Login** — `login`
- **Dashboard** — `dashboard`
- **Logout** — `logout`
- **Admin Applications** — `admin_applications`
- **Add Application** — `add_application`
- **Edit Application** — `edit_application`
- **Delete Application** — `delete_application`
- **Penn To Wordnet** — `penn_to_wordnet`
- **Get Sentiment Score** — `get_sentiment_score`
- **Review Page** — `review_page`

## Getting started

### 1. Get the project

```bash
git clone https://github.com/nasirabbas827/FraudApps-finalcode-Faraz-Noor.git
cd FraudApps-finalcode-Faraz-Noor
```

### 2. Prepare Python

Create an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows Command Prompt, or `source .venv/bin/activate` on macOS/Linux.

No requirements file is included. The inspected Python imports indicate these dependencies as a starting point:

```bash
python -m pip install Flask Flask-SQLAlchemy Flask-Login Flask-Bcrypt Werkzeug nltk
```

Dependency versions are not pinned in this repository.

### 3. Configure and run

Keep the included SQLite database files in their expected locations: [`instance/database.db`](instance/database.db).

Run from the repository root so relative file paths resolve correctly:

```bash
python app.py
```

Open http://127.0.0.1:5000/, or use the address printed by the application.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`app.py`](app.py) | Application entry point |
| [`instance`](instance) | Local Flask instance data |
| [`static`](static) | Static application assets |
| [`templates`](templates) | HTML page templates |

## Development notes

These setup instructions are based on the repository source. The application has not been executed as part of this documentation update; verify dependencies and configuration in your local environment.
