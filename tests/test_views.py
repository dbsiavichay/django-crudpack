import pytest
from django.test import RequestFactory

from crudpack import ModelPack, PackViews, packs
from crudpack.views import build_view
from tests.testapp.models import Author, Book, Publisher, Tag
from tests.testapp.packs import ExtraContextMixin

LIST_URL = "/crud/testapp/author/"


def pack_info(response):
    return response.context["pack_info"]


# List


def test_list_context(client, authors):
    response = client.get(LIST_URL)

    assert response.status_code == 200
    assert "testapp/author_list.html" in [t.name for t in response.templates]

    info = pack_info(response)
    assert info["title"] == "authors"
    assert info["app_name"] == "testapp"
    assert info["model_name"] == "author"
    assert info["paths"] == {"list": LIST_URL, "create": LIST_URL + "create/"}
    assert info["headers"] == {
        "name": "Full name",
        "email": "E-mail address",
        "shout": "Shout",
        "initials": "Initials",
        "book_count": "Book count",
        "bold_name": "Bold name",
    }

    instance, row = info["rows"][0]
    assert instance == authors[0]
    assert row["data"]["initials"]["value"] == "AL"
    assert row["data"]["book_count"] == {
        "value": 0,
        "label": "Book count",
        "type": "int",
    }
    assert row["paths"]["detail"] == f"{LIST_URL}{instance.pk}/detail/"


def test_list_pagination(client, authors):
    first = pack_info(client.get(LIST_URL))
    second = pack_info(client.get(LIST_URL, {"page": 2}))

    assert (first["start_index"], first["end_index"], first["count"]) == (1, 2, 4)
    assert (second["start_index"], second["end_index"], second["count"]) == (3, 4, 4)
    assert len(second["rows"]) == 2


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", 1), ("3", 3), ("50", 3), ("abc", 2), ("0", 2), ("-1", 2), ("", 2)],
)
def test_list_paginate_by_parameter(client, authors, value, expected):
    response = client.get(LIST_URL, {"paginate_by": value})

    assert response.status_code == 200
    assert len(pack_info(response)["rows"]) == expected


def test_list_without_pagination(client, db):
    info = pack_info(client.get("/crud/testapp/book/"))

    assert (info["start_index"], info["end_index"], info["count"]) == (0, 0, 0)
    assert info["rows"] == []


def test_list_escapes_values(client, db):
    Author.objects.create(name="<script>alert(1)</script>")

    content = client.get(LIST_URL).content.decode()

    assert "<script>" not in content
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in content
    # Values already marked safe (format_html) are rendered as HTML.
    assert "<b>&lt;script&gt;alert(1)&lt;/script&gt;</b>" in content


def test_user_mixins_run_after_crudpack_context(client, tag):
    response = client.get("/crud/testapp/tag/")

    assert isinstance(response.context["view"], ExtraContextMixin)
    assert response.context["extra"] == [
        "app_name",
        "count",
        "end_index",
        "headers",
        "model_name",
        "paths",
        "rows",
        "start_index",
        "title",
    ]


def test_list_queryset_option(db, authors):
    pack = ModelPack(Author, queryset=Author.objects.filter(name__startswith="A"))
    view = build_view(pack, PackViews.LIST).as_view()

    response = view(RequestFactory().get("/"))

    assert list(response.context_data["object_list"]) == authors[:2]


def test_list_accepts_a_list_as_queryset(db, authors):
    class ListQuerysetMixin:
        def get_queryset(self):
            return list(Author.objects.all())

    pack = ModelPack(Author, list_mixins=(ListQuerysetMixin,), list_template_name="x")
    view = build_view(pack, PackViews.LIST).as_view()

    info = view(RequestFactory().get("/")).context_data["pack_info"]

    assert (info["start_index"], info["end_index"], info["count"]) == (1, 4, 4)


def test_view_classes_are_built_once_per_pack():
    pack = packs.get_pack(Author)
    view_classes = {pattern.name: pattern.callback.view_class for pattern in pack.urls}

    assert view_classes["testapp_author_list"].__name__ == "AuthorListView"
    assert view_classes["testapp_author_list"].pack is pack
    assert pack.urls[0].callback.view_class is not view_classes["testapp_author_list"]


# Detail


def test_detail_context(client, author):
    response = client.get(f"{LIST_URL}{author.pk}/detail/")

    assert response.status_code == 200
    info = pack_info(response)
    assert set(info["paths"]) == {"list", "create", "update", "detail", "delete"}
    assert info["fields"]["email"] == {
        "value": "ada@example.com",
        "label": "E-mail address",
        "type": "charfield",
    }
    assert info["bs_fieldsets"] == [
        {
            "title": "Main",
            "fieldset": [
                {
                    "name": {**info["fields"]["name"], "cols": 6},
                    "email": {**info["fields"]["email"], "cols": 6},
                }
            ],
        },
        {
            "title": "Extra",
            "fieldset": [{"shout": {**info["fields"]["shout"], "cols": 12}}],
        },
    ]


def test_detail_renders_grouped_choices(client, book):
    response = client.get(f"/crud/testapp/book/{book.pk}/detail/")

    assert "Status: Out of print" in response.content.decode()
    assert "crud/detail.html" in [t.name for t in response.templates]


def test_detail_404(client, db):
    assert client.get(f"{LIST_URL}999/detail/").status_code == 404


# Create


def test_create_get(client, db):
    response = client.get("/crud/testapp/book/create/")

    assert response.status_code == 200
    assert type(response.context["form"]).__name__ == "BookForm"
    assert set(pack_info(response)["paths"]) == {"list", "create"}


def test_create_redirects_to_list(client, author):
    response = client.post(
        "/crud/testapp/book/create/",
        {"title": "New", "author": author.pk, "status": "pub", "pages": 3},
    )

    assert response.status_code == 302
    assert response["Location"] == "/crud/testapp/book/"
    assert Book.objects.get().title == "New"


def test_create_invalid(client, db):
    response = client.post("/crud/testapp/book/create/", {"title": ""})

    assert response.status_code == 200
    assert response.context["form"].errors["title"]
    assert not Book.objects.exists()


def test_create_without_list_redirects_to_detail(client, db):
    response = client.post(
        "/crud/testapp/publisher/create/", {"code": "acme", "name": "Acme"}
    )

    assert response.status_code == 302
    assert response["Location"] == "/crud/testapp/publisher/acme/detail/"
    assert Publisher.objects.filter(pk="acme").exists()


def test_default_success_url_is_formatted_with_the_object(db):
    pack = ModelPack(Author, default_success_url="/done/{id}/")
    view = build_view(pack, PackViews.CREATE).as_view()

    response = view(RequestFactory().post("/", {"name": "Ada"}))

    assert response.status_code == 302
    assert response["Location"] == f"/done/{Author.objects.get().pk}/"


# Update


def test_update(client, tag):
    url = f"/crud/testapp/tag/{tag.pk}/update/"

    assert client.get(url).status_code == 200

    response = client.post(url, {"name": "django"})

    assert response["Location"] == "/crud/testapp/tag/"
    tag.refresh_from_db()
    assert tag.name == "django"


def test_update_without_list_redirects_to_detail(client, publisher):
    response = client.post(
        "/crud/testapp/publisher/acme/update/", {"code": "acme", "name": "ACME"}
    )

    assert response["Location"] == "/crud/testapp/publisher/acme/detail/"


# Delete


def test_delete(client, author):
    url = f"{LIST_URL}{author.pk}/delete/"

    assert client.get(url).status_code == 200

    response = client.post(url)

    assert response["Location"] == LIST_URL
    assert not Author.objects.exists()


def test_delete_mixins_are_applied(client, tag, django_user_model):
    url = f"/crud/testapp/tag/{tag.pk}/delete/"

    response = client.post(url)

    assert response.status_code == 302
    assert response["Location"].startswith("/login/")
    assert Tag.objects.exists()

    client.force_login(django_user_model.objects.create_user("admin"))
    response = client.post(url)

    assert response["Location"] == "/crud/testapp/tag/"
    assert not Tag.objects.exists()
