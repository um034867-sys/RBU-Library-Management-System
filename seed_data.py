"""Optional demonstration data for the RBU Library Management System.

Usage:
    python seed_data.py

Creates the tables if needed, then inserts a small set of demonstration
members and books. It is idempotent and non-destructive:

- members are added only when no record with the same name and email exists
- books are added only when the ISBN is not already present
- existing records are never overwritten or deleted
"""

from app import DATABASE, init_db

DEMO_MEMBERS = [
    ("Rahul Sharma", "rahul.sharma@rbunagpur.in"),
    ("Priya Patel", "priya.patel@rbunagpur.in"),
    ("Karan Shah", "karan.shah@rbunagpur.in"),
    ("Karan Mehta", "karan.mehta@rbunagpur.in"),
    ("Rohan Gupta", "rohan.gupta@rbunagpur.in"),
]

DEMO_BOOKS = [
    ("Python Crash Course", "Eric Matthes", "9781593279288", "Programming"),
    ("Clean Code", "Robert C. Martin", "9780132350884", "Software Engineering"),
    ("Introduction to Algorithms", "Thomas H. Cormen", "9780262033848", "Algorithms"),
    ("Artificial Intelligence", "Stuart Russell", "9780136042594", "Artificial Intelligence"),
    ("Deep Learning", "Ian Goodfellow", "9780262035613", "Machine Learning"),
]


def main():
    import sqlite3

    init_db()
    db = sqlite3.connect(DATABASE)

    members_added = 0
    members_skipped = 0
    for name, email in DEMO_MEMBERS:
        exists = db.execute(
            "SELECT id FROM members WHERE name = ? AND email = ?", (name, email)
        ).fetchone()
        if exists:
            members_skipped += 1
            continue
        db.execute("INSERT INTO members (name, email) VALUES (?, ?)", (name, email))
        members_added += 1

    books_added = 0
    books_skipped = 0
    for title, author, isbn, category in DEMO_BOOKS:
        exists = db.execute("SELECT id FROM books WHERE isbn = ?", (isbn,)).fetchone()
        if exists:
            books_skipped += 1
            continue
        db.execute(
            "INSERT INTO books (title, author, isbn, category) VALUES (?, ?, ?, ?)",
            (title, author, isbn, category),
        )
        books_added += 1

    db.commit()
    db.close()

    print(f"Members: {members_added} added, {members_skipped} already present (skipped)")
    print(f"Books:   {books_added} added, {books_skipped} already present (skipped)")
    print(f"Database: {DATABASE}")


if __name__ == "__main__":
    main()