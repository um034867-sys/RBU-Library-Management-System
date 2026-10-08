# RBU Library Management System

A library management portal for **Ramdeobaba University, Nagpur**. Create members and books, autocomplete member search, and issue/return books — built as a plain HTML + CSS + Vanilla JavaScript frontend with a Flask REST API and SQLite persistence.

> This is an independent college/educational project. It is **not** an official Ramdeobaba University system.

## Features

- Book CRUD (add, list, search, delete)
- Member CRUD (add, list, delete)
- Member autocomplete (type-ahead, max 10 suggestions, no full-list download)
- Search books by title, author or ISBN
- Issue book to a selected member
- Return an issued book
- Visual `AVAILABLE` / `ISSUED` status indicators
- SQLite persistence
- Fetch API frontend (no page reloads during operations)
- Flask REST API
- RBU student email validation (`@rbunagpur.in`)
- RBU branding (official logo, watermark, institutional palette)

## Technology

- HTML
- CSS
- Vanilla JavaScript
- Fetch API
- Python Flask (backend)
- SQLite (database)
- Node.js/npm (frontend tooling only — checks and formatting)

## Project Structure

```
RBU-library-management/
├── app.py               # Flask application + REST API + SQLite setup
├── seed_data.py         # optional demonstration data (idempotent)
├── requirements.txt     # Python dependencies (Flask, pytest)
├── package.json         # Node.js/npm frontend tooling (formatting + checks)
├── pytest.ini           # pytest configuration (tests/ + repo root on path)
├── .gitignore           # ignores library.db, node_modules, caches, venvs, etc.
├── tests/
│   ├── conftest.py      # isolated temp SQLite database + client fixtures
│   └── test_app.py      # automated tests for the Flask REST API
├── templates/
│   └── index.html       # single-page frontend
└── static/
    ├── style.css        # RBU-themed styles (incl. watermark)
    ├── script.js        # frontend logic (autocomplete, CRUD, issue/return)
    └── img/
        └── rbu-logo.png # local official Ramdeobaba University logo
```

## Installation

```bash
# 1. Python dependencies (Flask, pytest)
python -m pip install -r requirements.txt

# 2. Node.js frontend tooling (Prettier)
npm install
```

Then start the application with:

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

The `library.db` file is created automatically on first run.

> Note: on some Windows setups `python` is a Microsoft Store alias. Use `py`
> instead if `python` is not found (e.g. `py -m pip install -r requirements.txt`,
> `py app.py`).

## Frontend tooling (Node.js/npm)

The Flask + SQLite backend is unchanged — npm is used **only** to lint/format
the plain HTML/CSS/JavaScript frontend:

| Command            | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| `npm run check`    | JS syntax check + Prettier format check          |
| `npm run format:check` | Verify frontend files match Prettier style   |
| `npm run format`   | Reformat frontend files with Prettier (`--write`)|

## Automated tests

The test suite (`tests/`) exercises the real Flask REST API through Flask's
test client. Every test uses a throwaway SQLite database in a temporary
folder — your real `library.db` is never touched.

```bash
python -m pytest
# or, if `python` is not on PATH:
py -m pytest
```

Covered: the index page, add/list/search books, issue/return rules, delete,
duplicate ISBN and required-field validation, and member handling.

## RBU Email

Member emails are normalized to the university domain `@rbunagpur.in`:

| Input | Stored |
| ----- | ------ |
| `rahul.sharma` | `rahul.sharma@rbunagpur.in` |
| `rahul.sharma@rbunagpur.in` | `rahul.sharma@rbunagpur.in` (never duplicated) |
| `RAHUL.SHARMA` | `rahul.sharma@rbunagpur.in` (normalized to lowercase) |
| `rahul.sharma@gmail.com` | rejected — "Please use your RBU student email" |

Non-RBU domains are rejected. Empty email remains optional.

## Database

SQLite is used for persistence. The database file `library.db` is created automatically
on start and is intentionally **ignored by Git** (`*.db` in `.gitignore`) because it
contains local/working data. A fresh clone gets an empty database on first run.

## Demo Data

To populate the application with a small demonstration set of members and books
(no duplicates, existing data is never overwritten or deleted):

```bash
python seed_data.py
```

Demonstration members use `@rbunagpur.in` emails (Rahul Sharma, Priya Patel,
Karan Shah, Karan Mehta, Rohan Gupta) and the books include *Python Crash Course*,
*Clean Code*, *Introduction to Algorithms*, *Artificial Intelligence* and
*Deep Learning*.

## API endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/books` | List all books |
| POST | `/api/books` | Add a book |
| GET | `/api/books/search?q=...` | Search books by title, author or ISBN |
| POST | `/api/books/<id>/issue` | Issue a book to a member |
| POST | `/api/books/<id>/return` | Return an issued book |
| DELETE | `/api/books/<id>` | Delete a book |
| GET | `/api/members` | List all members |
| GET | `/api/members/search?q=...` | Search members by name (max 10 results) |
| POST | `/api/members` | Add a member (accepts local-part or full RBU email) |
| DELETE | `/api/members/<id>` | Delete a member (only if no books are issued to them) |

All requests/responses are JSON.

## Limitations

This project uses SQLite plus the Flask development server and is intended for
local/educational use — not a production, university-wide deployment.