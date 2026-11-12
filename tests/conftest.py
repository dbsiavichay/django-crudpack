import pytest

from tests.testapp.models import Author, Book, Publisher, Tag


@pytest.fixture
def author(db):
    return Author.objects.create(name="Ada Lovelace", email="ada@example.com")


@pytest.fixture
def authors(db):
    return [
        Author.objects.create(name=name)
        for name in ("Ada Lovelace", "Alan Turing", "Grace Hopper", "Edsger Dijkstra")
    ]


@pytest.fixture
def book(author):
    return Book.objects.create(
        title="Notes",
        author=author,
        status="oop",
        pages=120,
        metadata={"color": "blue", "size": {"w": 10}},
    )


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="python")


@pytest.fixture
def publisher(db):
    return Publisher.objects.create(code="acme", name="Acme")
