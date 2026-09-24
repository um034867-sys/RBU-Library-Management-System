import os
import re
import sqlite3
from flask import Flask, jsonify, request, render_template, g, abort

app = Flask(__name__)

# Path to the SQLite database file
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


# ---------- Database helpers ----------
def get_db():
    """Return a connection to the SQLite database (one per request)."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    """Close the database connection after each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create database tables if they do not exist."""
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            category TEXT,
            available INTEGER NOT NULL DEFAULT 1,
            issued_to INTEGER,
            FOREIGN KEY (issued_to) REFERENCES members(id)
        );
        """
    )
    db.commit()
    db.close()


# ---------- Helper converters ----------
def book_to_dict(row):
    """Convert a book row into a JSON-friendly dict, including member name."""
    book = dict(row)
    if book.get("issued_to"):
        member = get_db().execute(
            "SELECT name FROM members WHERE id = ?", (book["issued_to"],)
        ).fetchone()
        book["issued_to_name"] = member["name"] if member else "Unknown"
    else:
        book["issued_to_name"] = None
    book["available"] = bool(book["available"])
    return book


def get_book_or_404(book_id):
    """Fetch a book by id or abort with 404."""
    book = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        abort(404, description="Book not found")
    return book


def get_member_or_404(member_id):
    """Fetch a member by id or abort with 404."""
    member = get_db().execute(
        "SELECT * FROM members WHERE id = ?", (member_id,)
    ).fetchone()
    if member is None:
        abort(404, description="Member not found")
    return member


# ---------- RBU student email handling ----------
RBU_EMAIL_DOMAIN = "rbunagpur.in"
_LOCAL_RE = re.compile(r"^[a-z0-9._-]+$")


def normalize_rbu_email(raw):
    """Normalize a student email to <local>@rbunagpur.in.

    - "rahul.sharma"               -> "rahul.sharma@rbunagpur.in"
    - "rahul.sharma@rbunagpur.in"  -> "rahul.sharma@rbunagpur.in" (never duplicated)
    - "RAHUL.SHARMA"               -> "rahul.sharma@rbunagpur.in"
    - "" / None                    -> None (email stays optional)
    - "rahul.sharma@gmail.com"     -> raises ValueError
    """
    value = (raw or "").strip().lower()
    if not value:
        return None

    if "@" in value:
        parts = value.split("@")
        if len(parts) != 2 or parts[1] != RBU_EMAIL_DOMAIN or not parts[0]:
            raise ValueError(
                "Please use your RBU student email (e.g. rahul.sharma or rahul.sharma@rbunagpur.in)"
            )
        local = parts[0]
    else:
        local = value

    if not _LOCAL_RE.match(local):
        raise ValueError(
            "Invalid email. Use letters, numbers, dots, dashes or underscores only."
        )
    return f"{local}@{RBU_EMAIL_DOMAIN}"


# ---------- Books API ----------
@app.route("/api/books", methods=["GET"])
def list_books():
    """Return all books."""
    rows = get_db().execute("SELECT * FROM books ORDER BY id").fetchall()
    return jsonify([book_to_dict(r) for r in rows])


@app.route("/api/books", methods=["POST"])
def add_book():
    """Add a new book."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    isbn = (data.get("isbn") or "").strip()
    category = (data.get("category") or "").strip()

    # Validation: required fields cannot be empty
    if not title or not author or not isbn:
        abort(400, description="Title, author and ISBN are required")

    # ISBN must be unique
    existing = get_db().execute(
        "SELECT id FROM books WHERE isbn = ?", (isbn,)
    ).fetchone()
    if existing:
        abort(400, description="ISBN already exists")

    cur = get_db().execute(
        "INSERT INTO books (title, author, isbn, category) VALUES (?, ?, ?, ?)",
        (title, author, isbn, category),
    )
    get_db().commit()
    book = get_db().execute(
        "SELECT * FROM books WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(book_to_dict(book)), 201


@app.route("/api/books/search", methods=["GET"])
def search_books():
    """Search books by title, author or ISBN."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    rows = get_db().execute(
        """SELECT * FROM books
           WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
           ORDER BY id""",
        (like, like, like),
    ).fetchall()
    return jsonify([book_to_dict(r) for r in rows])


@app.route("/api/books/<int:book_id>/issue", methods=["POST"])
def issue_book(book_id):
    """Issue a book to a member."""
    book = get_book_or_404(book_id)

    # A book cannot be issued if it is not available
    if not book["available"]:
        abort(400, description="Book is already issued")

    data = request.get_json(silent=True) or {}
    member_id = data.get("member_id")
    if member_id is None:
        abort(400, description="Member ID is required")
    try:
        member_id = int(member_id)
    except (TypeError, ValueError):
        abort(400, description="Member ID must be a number")

    # Member must exist
    get_member_or_404(member_id)

    get_db().execute(
        "UPDATE books SET available = 0, issued_to = ? WHERE id = ?",
        (member_id, book_id),
    )
    get_db().commit()
    book = get_db().execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    return jsonify({"message": "Book issued successfully", "book": book_to_dict(book)})


@app.route("/api/books/<int:book_id>/return", methods=["POST"])
def return_book(book_id):
    """Return an issued book."""
    book = get_book_or_404(book_id)

    # A book can only be returned if it is currently issued
    if book["available"]:
        abort(400, description="Book is not currently issued")

    get_db().execute(
        "UPDATE books SET available = 1, issued_to = NULL WHERE id = ?", (book_id,)
    )
    get_db().commit()
    book = get_db().execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    return jsonify({"message": "Book returned successfully", "book": book_to_dict(book)})


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    """Delete a book by id."""
    get_book_or_404(book_id)
    get_db().execute("DELETE FROM books WHERE id = ?", (book_id,))
    get_db().commit()
    return jsonify({"message": "Book deleted successfully"})


# ---------- Members API ----------
@app.route("/api/members", methods=["GET"])
def list_members():
    """Return all members."""
    rows = get_db().execute("SELECT * FROM members ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/members/search", methods=["GET"])
def search_members():
    """Search members by name (case-insensitive, partial). Returns at most 10."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    rows = get_db().execute(
        """SELECT id, name, email FROM members
           WHERE name LIKE ?
           ORDER BY CASE WHEN name LIKE ? THEN 0 ELSE 1 END, name
           LIMIT 10""",
        (like, f"{q}%"),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/members", methods=["POST"])
def add_member():
    """Add a new member with an RBU student email (@rbunagpur.in)."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    try:
        email = normalize_rbu_email(data.get("email"))
    except ValueError as exc:
        abort(400, description=str(exc))

    if not name:
        abort(400, description="Member name is required")

    cur = get_db().execute(
        "INSERT INTO members (name, email) VALUES (?, ?)", (name, email)
    )
    get_db().commit()
    member = get_db().execute(
        "SELECT * FROM members WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(dict(member)), 201


@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    """Delete a member by id. Blocked while the member still has books issued."""
    get_member_or_404(member_id)
    issued = get_db().execute(
        "SELECT COUNT(*) AS n FROM books WHERE issued_to = ?", (member_id,)
    ).fetchone()["n"]
    if issued:
        abort(400, description="Member still has issued books. Return them first.")
    get_db().execute("DELETE FROM members WHERE id = ?", (member_id,))
    get_db().commit()
    return jsonify({"message": "Member deleted successfully"})


# ---------- Error handling ----------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(400)
def bad_request(e):
    message = getattr(e, "description", "Bad request")
    return jsonify({"error": message}), 400


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ---------- Frontend ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)