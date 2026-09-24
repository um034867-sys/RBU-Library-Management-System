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
- Python Flask
- SQLite

## Project Structure

```
RBU-library-management/
├── app.py               # Flask application + REST API + SQLite setup
├── seed_data.py         # optional demonstration data (idempotent)
├── requirements.txt     # Python dependencies (Flask)
├── .gitignore           # ignores library.db, caches, venvs, etc.
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
git clone <repository-url>
cd RBU-library-management
python -m pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

The `library.db` file is created automatically on first run.

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