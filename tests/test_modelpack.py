import pytest
from django.core.exceptions import ImproperlyConfigured

from crudpack import ModelPack, PackViews
from tests.testapp.models import Author, Book, Novel, Publisher, Tag


def test_defaults():
    pack = ModelPack(Author)

    assert pack.fields == "__all__"
    assert pack.list_fields == ("__str__",)
    assert pack.detail_fields == ("id", "name", "email")
    assert pack.allowed_views == tuple(PackViews)
    assert pack.queryset is None


def test_model_can_be_declared_on_the_class():
    class AuthorPack(ModelPack):
        model = Author

    assert AuthorPack().model is Author


def test_model_is_required():
    with pytest.raises(ImproperlyConfigured, match="requires a Django model"):
        ModelPack()


def test_options_passed_as_kwargs_are_validated():
    with pytest.raises(ImproperlyConfigured, match="'list_fields'"):
        ModelPack(Author, list_fields="name")


def test_unknown_options_are_rejected():
    with pytest.raises(ImproperlyConfigured, match="invalid option 'colour'"):
        ModelPack(Author, colour="red")

    with pytest.raises(ImproperlyConfigured, match="invalid option '_validate'"):
        ModelPack(Author, _validate=None)


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"list_fields": {"a": "name"}}, "cannot be a dict"),
        ({"list_fields": ()}, "cannot be empty"),
        ({"list_fields": ("missing",)}, "no field, method or property named 'missing'"),
        ({"list_fields": (1,)}, "must be strings"),
        ({"detail_fields": "name"}, "'detail_fields'"),
        ({"detail_fields": {"Main": ("nope",)}}, "named 'nope'"),
        ({"default_labels": ()}, "'default_labels' option must be a dict"),
        ({"inlines": []}, "'inlines' option must be a dict"),
        ({"list_mixins": object}, "'list_mixins' option must be a tuple"),
        ({"form_class": object, "fields": ("name",)}, "either 'form_class' or"),
        ({"queryset": []}, "must be a QuerySet"),
        ({"paginate_by": 0}, "'paginate_by' option must be a positive integer"),
        ({"max_paginate_by": "10"}, "'max_paginate_by' option must be a positive"),
        ({"allowed_views": ()}, "non-empty list or tuple"),
        ({"allowed_views": "list"}, "non-empty list or tuple"),
        ({"allowed_views": ("list",)}, "PackViews members"),
    ],
)
def test_invalid_options(options, message):
    with pytest.raises(ImproperlyConfigured, match=message):
        ModelPack(Author, **options)


def test_field_names_accept_methods_properties_and_paths():
    pack = ModelPack(
        Book,
        list_fields=("__str__", "author__name", "metadata__color", "cover"),
    )

    assert pack.list_fields[1] == "author__name"
    assert ModelPack(Author, list_fields=("shout", "initials", "books"))


def test_duplicate_allowed_views_are_removed():
    pack = ModelPack(Author, allowed_views=[PackViews.LIST, PackViews.LIST])

    assert pack.allowed_views == (PackViews.LIST,)


@pytest.mark.parametrize(
    "allowed_views",
    [(PackViews.DELETE,), (PackViews.DETAIL, PackViews.DELETE)],
)
def test_delete_needs_somewhere_to_redirect(allowed_views):
    with pytest.raises(ImproperlyConfigured, match="delete view needs"):
        ModelPack(Author, allowed_views=allowed_views)


@pytest.mark.parametrize("view", [PackViews.CREATE, PackViews.UPDATE])
def test_create_and_update_need_somewhere_to_redirect(view):
    with pytest.raises(ImproperlyConfigured, match="create and update views need"):
        ModelPack(Author, allowed_views=(view,))


@pytest.mark.parametrize(
    "options",
    [
        {"allowed_views": (PackViews.CREATE, PackViews.DETAIL)},
        {"allowed_views": (PackViews.DELETE,), "default_success_url": "/"},
        {"allowed_views": (PackViews.DETAIL,)},
    ],
)
def test_valid_success_url_configurations(options):
    assert ModelPack(Author, **options)


@pytest.mark.parametrize(
    ("model", "converter"),
    [(Author, "int"), (Tag, "uuid"), (Publisher, "str"), (Novel, "int")],
)
def test_pk_converter(model, converter):
    assert ModelPack(model).get_pk_converter() == converter


def test_routes():
    pack = ModelPack(Tag)

    assert [pack.get_route(view) for view in PackViews] == [
        "",
        "create/",
        "<uuid:pk>/update/",
        "<uuid:pk>/detail/",
        "<uuid:pk>/delete/",
    ]


def test_url_names_use_the_namespace_and_suffixes():
    pack = ModelPack(Author, namespace="backoffice", url_list_suffix="index")

    assert pack.get_base_url_name(PackViews.LIST) == "testapp_author_index"
    assert pack.get_base_url_name("detail") == "testapp_author_detail"
    assert pack.get_url_name(PackViews.LIST) == "backoffice:testapp_author_index"


def test_template_names():
    pack = ModelPack(
        Author,
        list_template_name="l.html",
        form_template_name="f.html",
        detail_template_name="d.html",
    )

    assert pack.get_template_name(PackViews.LIST) == "l.html"
    assert pack.get_template_name(PackViews.CREATE) == "f.html"
    assert pack.get_template_name(PackViews.UPDATE) == "f.html"
    assert pack.get_template_name(PackViews.DETAIL) == "d.html"
    assert pack.get_template_name(PackViews.DELETE) is None


def test_mixins_per_view():
    class A:
        pass

    class B:
        pass

    pack = ModelPack(Author, create_mixins=[A], update_mixins=(B,))

    assert pack.get_mixins(PackViews.CREATE) == (A,)
    assert pack.get_mixins(PackViews.UPDATE) == (B,)
    assert pack.get_mixins(PackViews.LIST) == ()
