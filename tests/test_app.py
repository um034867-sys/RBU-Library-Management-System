"""Automated tests for the existing Flask REST API.

These tests exercise the real application code (`app.py`) through Flask's
test client. Nothing is mocked or faked; the only isolation is the temporary
database provided by the `client` fixture in conftest.py.
"""


# ---------- Frontend ----------
def test_index_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.content_type
    body = res.get_data(as_text=True)
    assert "Library Management System" in body
    assert "/static/script.js" in body


def test_static_script_is_served(client):
    res = client.get("/static/script.js")
    assert res.status_code == 200


# ---------- List / add books ----------
def test_list_books_starts_empty(client):
    res = client.get("/api/books")
    assert res.status_code == 200
    assert res.get_json() == []


def test_add_book(client):
    res = client.post(
        "/api/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "9780132350884",
            "category": "Software Engineering",
        },
    )
    assert res.status_code == 201
    book = res.get_json()
    assert book["title"] == "Clean Code"
    assert book["isbn"] == "9780132350884"
    assert book["available"] is True
    assert book["issued_to"] is None

    listing = client.get("/api/books").get_json()
    assert len(listing) == 1
    assert listing[0]["id"] == book["id"]


def test_add_book_missing_required_fields(client):
    # Missing title
    res = client.post(
        "/api/books", json={"author": "Someone", "isbn": "111"}
    )
    assert res.status_code == 400
    # Missing author
    res = client.post("/api/books", json={"title": "T", "isbn": "222"})
    assert res.status_code == 400
    # Missing ISBN
    res = client.post("/api/books", json={"title": "T", "author": "A"})
    assert res.status_code == 400
    # Empty body
    res = client.post("/api/books", json={})
    assert res.status_code == 400
    # Nothing persisted
    assert client.get("/api/books").get_json() == []


def test_add_book_duplicate_isbn(client):
    payload = {"title": "First", "author": "A", "isbn": "9780000000001"}
    assert client.post("/api/books", json=payload).status_code == 201

    res = client.post(
        "/api/books", json={"title": "Second", "author": "B", "isbn": "9780000000001"}
    )
    assert res.status_code == 400
    assert "ISBN" in res.get_json()["error"]
    assert len(client.get("/api/books").get_json()) == 1


# ---------- Search ----------
def test_search_by_title(client, make_book):
    make_book(title="Clean Code", author="Robert C. Martin", isbn="9780132350884")
    make_book(title="Deep Learning", author="Ian Goodfellow", isbn="9780262035613")

    res = client.get("/api/books/search?q=Clean")
    assert res.status_code == 200
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Clean Code"


def test_search_by_author(client, make_book):
    make_book(title="Clean Code", author="Robert C. Martin", isbn="9780132350884")
    make_book(title="Deep Learning", author="Ian Goodfellow", isbn="9780262035613")

    res = client.get("/api/books/search?q=goodfellow")
    assert res.status_code == 200
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["author"] == "Ian Goodfellow"


def test_search_by_isbn(client, make_book):
    make_book(title="Clean Code", author="Robert C. Martin", isbn="9780132350884")
    make_book(title="Deep Learning", author="Ian Goodfellow", isbn="9780262035613")

    res = client.get("/api/books/search?q=9780262035613")
    assert res.status_code == 200
    results = res.get_json()
    assert len(results) == 1
    assert results[0]["isbn"] == "9780262035613"


def test_search_no_match_returns_empty(client, make_book):
    make_book()
    assert client.get("/api/books/search?q=zzzz").get_json() == []


def test_search_empty_query_returns_empty(client, make_book):
    make_book()
    assert client.get("/api/books/search?q=").get_json() == []


# ---------- Issue ----------
def test_issue_available_book(client, make_book, member):
    book = make_book()

    res = client.post(
        f"/api/books/{book['id']}/issue", json={"member_id": member["id"]}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Book issued successfully"
    assert data["book"]["available"] is False
    assert data["book"]["issued_to"] == member["id"]
    assert data["book"]["issued_to_name"] == member["name"]

    listed = client.get("/api/books").get_json()[0]
    assert listed["available"] is False


def test_issue_already_issued_book_is_rejected(client, make_book, member):
    book = make_book()
    assert (
        client.post(
            f"/api/books/{book['id']}/issue", json={"member_id": member["id"]}
        ).status_code
        == 200
    )

    res = client.post(
        f"/api/books/{book['id']}/issue", json={"member_id": member["id"]}
    )
    assert res.status_code == 400
    assert "already issued" in res.get_json()["error"]


def test_issue_nonexistent_book_returns_404(client, member):
    res = client.post("/api/books/99999/issue", json={"member_id": member["id"]})
    assert res.status_code == 404


def test_issue_with_nonexistent_member_returns_404(client, make_book):
    book = make_book()
    res = client.post(f"/api/books/{book['id']}/issue", json={"member_id": 99999})
    assert res.status_code == 404
    # Book must remain available after the failed issue
    assert client.get("/api/books").get_json()[0]["available"] is True


def test_issue_without_member_id_returns_400(client, make_book):
    book = make_book()
    res = client.post(f"/api/books/{book['id']}/issue", json={})
    assert res.status_code == 400
    assert "Member ID" in res.get_json()["error"]


def test_issue_with_non_numeric_member_id_returns_400(client, make_book):
    book = make_book()
    res = client.post(f"/api/books/{book['id']}/issue", json={"member_id": "abc"})
    assert res.status_code == 400


# ---------- Return ----------
def test_return_issued_book(client, make_book, member):
    book = make_book()
    client.post(f"/api/books/{book['id']}/issue", json={"member_id": member["id"]})

    res = client.post(f"/api/books/{book['id']}/return")
    assert res.status_code == 200
    data = res.get_json()
    assert data["message"] == "Book returned successfully"
    assert data["book"]["available"] is True
    assert data["book"]["issued_to"] is None
    assert data["book"]["issued_to_name"] is None


def test_return_book_that_is_not_issued_is_rejected(client, make_book):
    book = make_book()
    res = client.post(f"/api/books/{book['id']}/return")
    assert res.status_code == 400
    assert "not currently issued" in res.get_json()["error"]


def test_return_nonexistent_book_returns_404(client):
    res = client.post("/api/books/99999/return")
    assert res.status_code == 404


# ---------- Delete ----------
def test_delete_book(client, make_book):
    book = make_book()
    res = client.delete(f"/api/books/{book['id']}")
    assert res.status_code == 200
    assert client.get("/api/books").get_json() == []


def test_delete_nonexistent_book_returns_404(client):
    res = client.delete("/api/books/99999")
    assert res.status_code == 404


# ---------- Members ----------
def test_add_member_and_list(client):
    res = client.post(
        "/api/members", json={"name": "Rahul Sharma", "email": "rahul.sharma"}
    )
    assert res.status_code == 201
    member = res.get_json()
    assert member["email"] == "rahul.sharma@rbunagpur.in"

    listing = client.get("/api/members").get_json()
    assert len(listing) == 1
    assert listing[0]["name"] == "Rahul Sharma"


def test_add_member_rejects_non_rbu_email(client):
    res = client.post(
        "/api/members", json={"name": "Someone", "email": "someone@gmail.com"}
    )
    assert res.status_code == 400


def test_add_member_requires_name(client):
    res = client.post("/api/members", json={"name": "   "})
    assert res.status_code == 400


def test_delete_nonexistent_member_returns_404(client):
    assert client.delete("/api/members/99999").status_code == 404
