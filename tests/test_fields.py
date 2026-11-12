import pytest
from django.utils.safestring import SafeData

from crudpack import ModelPack, packs
from crudpack.services import FieldService
from crudpack.services.fields import flatten
from tests.testapp.models import Author, Book


@pytest.fixture
def book_service():
    return FieldService(packs.get_pack(Book))


@pytest.fixture
def author_service():
    return FieldService(packs.get_pack(Author))


def test_str(book_service, book):
    assert book_service.get_field_data(book, "__str__") == {
        "value": book,
        "label": "Book",
        "type": "book",
    }


def test_foreign_key_and_path_through_it(book_service, book):
    assert book_service.get_field_data(book, "author") == {
        "value": book.author,
        "label": "Author",
        "type": "foreignkey",
    }
    assert book_service.get_field_data(book, "author__name") == {
        "value": "Ada Lovelace",
        "label": "Name",
        "type": "charfield",
    }


def test_path_through_null_foreign_key(book_service, db):
    book = Book.objects.create(title="Orphan")

    assert book_service.get_field_data(book, "author__name")["value"] is None


def test_grouped_choices_use_the_display_value(book_service, book):
    data = book_service.get_field_data(book, "status")

    assert data == {"value": "Out of print", "label": "Status", "type": "charfield"}


def test_file_field(book_service, book):
    assert book_service.get_field_data(book, "cover")["value"] is None

    book.cover.name = "covers/notes.pdf"

    assert book_service.get_field_data(book, "cover") == {
        "value": {"name": "covers/notes.pdf", "url": "/media/covers/notes.pdf"},
        "label": "Cover",
        "type": "filefield",
    }


@pytest.mark.parametrize(
    ("path", "value", "field_type"),
    [
        ("metadata__color", "blue", "str"),
        ("metadata__size__w", 10, "int"),
        ("metadata__missing", None, "nonetype"),
        ("metadata__missing__deeper", None, "nonetype"),
        ("metadata", {"color": "blue", "size": {"w": 10}}, "jsonfield"),
    ],
)
def test_json_paths(book_service, book, path, value, field_type):
    data = book_service.get_field_data(book, path)

    assert (data["value"], data["type"]) == (value, field_type)


def test_json_path_label_uses_the_last_key(book_service):
    assert book_service.get_field_label("metadata__color") == "Color"


def test_methods_and_properties(author_service, author):
    assert author_service.get_field_data(author, "initials")["value"] == "AL"
    assert author_service.get_field_data(author, "book_count") == {
        "value": 0,
        "label": "Book count",
        "type": "int",
    }
    assert author_service.get_field_data(author, "shout") == {
        "value": "ADA LOVELACE",
        "label": "Shout",
        "type": "str",
    }


def test_path_through_a_plain_object(author_service, author):
    assert author_service.get_field_data(author, "shout__lower") == {
        "value": "ada lovelace",
        "label": "Lower",
        "type": "str",
    }


def test_values_are_not_marked_safe(author_service, db):
    author = Author.objects.create(name="<i>{0}</i>")

    shout = author_service.get_field_data(author, "shout")["value"]
    bold = author_service.get_field_data(author, "bold_name")["value"]

    assert shout == "<I>{0}</I>"
    assert not isinstance(shout, SafeData)
    assert isinstance(bold, SafeData)
    assert bold == "<b>&lt;i&gt;{0}&lt;/i&gt;</b>"


def test_related_managers_are_not_called(db, author):
    service = FieldService(ModelPack(Author, list_fields=("books",)))

    value = service.get_field_data(author, "books")["value"]

    assert list(value.all()) == []


def test_missing_attribute(author_service, author):
    with pytest.raises(AttributeError, match="has no attribute 'nope'"):
        author_service.get_field_data(author, "nope")


def test_labels(author_service):
    assert author_service.get_field_label("name") == "Full name"
    assert author_service.get_field_label("email") == "E-mail address"
    assert author_service.get_field_label("__str__") == "Author"
    assert author_service.get_field_label("book_count") == "Book count"


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        ("name", ["name"]),
        (("a", ("b", "c"), ["d"]), ["a", "b", "c", "d"]),
        ({"x": ("a", ("b", "c")), "y": "d"}, ["a", "b", "c", "d"]),
    ],
)
def test_flatten_field_names(names, expected):
    assert FieldService.get_flatten_field_names(names) == expected


def test_flatten():
    assert flatten(["a", ("b",), "c"]) == ["a", "b", "c"]


def test_bootstrap_fields_do_not_mutate_the_data():
    data = {"a": {"value": 1}, "b": {"value": 2}, "c": {"value": 3}}

    rows = FieldService.get_bootstrap_fields(("a", ("b", "c")), data)

    assert rows == [
        {"a": {"value": 1, "cols": 12}},
        {"b": {"value": 2, "cols": 6}, "c": {"value": 3, "cols": 6}},
    ]
    assert "cols" not in data["a"]
    assert FieldService.get_bootstrap_fields("a", data) == [
        {"a": {"value": 1, "cols": 12}}
    ]


def test_detail_data_with_rows(book_service, book):
    data, fieldsets = book_service.get_detail_data(book)

    assert list(data) == ["title", "status", "pages", "cover"]
    assert fieldsets == [
        {
            "title": "",
            "fieldset": [
                {"title": {**data["title"], "cols": 12}},
                {
                    "status": {**data["status"], "cols": 6},
                    "pages": {**data["pages"], "cols": 6},
                },
                {"cover": {**data["cover"], "cols": 12}},
            ],
        }
    ]
