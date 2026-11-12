import pytest
from django import forms
from django.test import RequestFactory

from crudpack import ModelPack, PackViews
from crudpack.mixins import Inline
from crudpack.views import build_view
from tests.testapp.models import Author, Book

CREATE_URL = "/crud/testapp/author/create/"


def management(total=1, initial=0, prefix="books"):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def test_inlines_in_context(client, db):
    response = client.get(CREATE_URL)

    inline = response.context["pack_info"]["inlines"]["books"]
    assert isinstance(inline, Inline)
    assert inline.formset.prefix == "books"
    assert inline.headers == ["Title", "Pages"]


def test_create_with_inlines(client, db):
    response = client.post(
        CREATE_URL,
        {"name": "Ada", **management(), "books-0-title": "Notes", "books-0-pages": "9"},
    )

    assert response.status_code == 302
    book = Book.objects.get()
    assert (book.title, book.author.name) == ("Notes", "Ada")


def test_invalid_inline_saves_nothing(client, db):
    response = client.post(
        CREATE_URL,
        {"name": "Ada", **management(), "books-0-title": "N", "books-0-pages": "x"},
    )

    assert response.status_code == 200
    inline = response.context["pack_info"]["inlines"]["books"]
    assert inline.errors[0]["pages"]
    # Inline errors are not mixed into the main form errors.
    assert not response.context["form"].errors
    assert not Author.objects.exists()


def test_invalid_form_with_valid_inline_saves_nothing(client, db):
    response = client.post(
        CREATE_URL,
        {"name": "", **management(), "books-0-title": "N", "books-0-pages": "1"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["name"]
    assert response.context["pack_info"]["inlines"]["books"].formset.is_bound
    assert not Book.objects.exists()


def test_update_with_inlines(client, book):
    url = f"/crud/testapp/author/{book.author.pk}/update/"

    response = client.get(url)

    formset = response.context["pack_info"]["inlines"]["books"].formset
    assert formset.instance == book.author
    assert formset.forms[0].instance == book

    response = client.post(
        url,
        {
            "name": "Ada L.",
            **management(total=2, initial=1),
            "books-0-id": book.pk,
            "books-0-author": book.author.pk,
            "books-0-title": "Renamed",
            "books-0-pages": "1",
            "books-1-title": "",
            "books-1-pages": "0",
        },
    )

    assert response.status_code == 302
    book.refresh_from_db()
    assert book.title == "Renamed"
    assert book.author.name == "Ada L."


def test_non_form_errors(db):
    formset = forms.inlineformset_factory(
        Author, Book, fields=("title",), max_num=1, validate_max=True
    )
    pack = ModelPack(Author, inlines={"books": formset})
    view = build_view(pack, PackViews.CREATE).as_view()
    data = {
        "name": "Ada",
        **management(total=2),
        "books-0-title": "One",
        "books-1-title": "Two",
    }

    response = view(RequestFactory().post("/", data))

    assert response.status_code == 200
    inline = response.context_data["pack_info"]["inlines"]["books"]
    assert inline.non_form_errors
    assert not Author.objects.exists()


def test_save_is_atomic(db):
    class FailingPack(ModelPack):
        inlines = {
            "books": forms.inlineformset_factory(Author, Book, fields=("title",))
        }

        def post_save_inlines(self, instance):
            assert instance.books.count() == 1
            raise RuntimeError("boom")

    view = build_view(FailingPack(Author), PackViews.CREATE).as_view()
    data = {"name": "Ada", **management(), "books-0-title": "One"}

    with pytest.raises(RuntimeError, match="boom"):
        view(RequestFactory().post("/", data))

    assert not Author.objects.exists()
    assert not Book.objects.exists()


def test_post_save_inlines_hook(db):
    saved = []

    class HookPack(ModelPack):
        inlines = {
            "books": forms.inlineformset_factory(Author, Book, fields=("title",))
        }

        def post_save_inlines(self, instance):
            saved.append(instance)

    view = build_view(HookPack(Author), PackViews.CREATE).as_view()

    view(RequestFactory().post("/", {"name": "Ada", **management(total=0)}))

    assert saved == [Author.objects.get()]
