"""Pytest fixtures for the RBU Library Management System tests.

Every test runs against a throwaway SQLite database in a temporary folder.
`app.DATABASE` is patched before the database is initialised, so the real
`library.db` is never opened, modified or deleted by the test suite.
"""

import pytest

import app as app_module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Flask test client backed by an isolated temporary database."""
    db_file = tmp_path / "test_library.db"
    monkeypatch.setattr(app_module, "DATABASE", str(db_file))
    app_module.app.config["TESTING"] = True
    app_module.init_db()
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def member(client):
    """A member created through the real API, returned as its JSON dict."""
    res = client.post(
        "/api/members",
        json={"name": "Test Student", "email": "test.student"},
    )
    assert res.status_code == 201
    return res.get_json()


@pytest.fixture()
def make_book(client):
    """Factory that adds a book through the real API and returns its JSON."""

    def _make_book(
        title="Python Crash Course",
        author="Eric Matthes",
        isbn="9781593279288",
        category="Programming",
    ):
        res = client.post(
            "/api/books",
            json={
                "title": title,
                "author": author,
                "isbn": isbn,
                "category": category,
            },
        )
        assert res.status_code == 201
        return res.get_json()

    return _make_book
