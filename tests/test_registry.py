import pytest
from django.core.exceptions import ImproperlyConfigured

from crudpack import ModelPack, PackService, packs, register
from tests.testapp.models import Author, Book, Publisher, Tag, TimeStamped


def test_autodiscover_registers_the_packs_module_of_each_app():
    for model in (Author, Book, Tag, Publisher):
        assert packs.is_registered(model)

    assert packs.is_registered("testapp.Book")
    assert type(packs.get_pack(Author)).__name__ == "AuthorPack"


def test_register_without_pack_class_uses_model_pack():
    site = PackService(name="other")

    pack = site.register(Author)

    assert type(pack) is ModelPack
    assert pack.model is Author
    assert pack.namespace == "other"
    assert site.get_pack("testapp.Author") is pack


def test_register_accepts_app_label_dot_model_name():
    site = PackService()

    site.register("testapp.Tag")

    assert site.is_registered(Tag)


@pytest.mark.parametrize("model", ["testapp.Missing", "nodot", "a.b.c"])
def test_register_unknown_model_string(model):
    with pytest.raises(ImproperlyConfigured, match="Cannot resolve model"):
        PackService().register(model)


@pytest.mark.parametrize("model", [None, object, 42])
def test_register_rejects_non_models(model):
    with pytest.raises(ImproperlyConfigured, match="is not a Django model"):
        PackService().register(model)


def test_register_rejects_abstract_models():
    with pytest.raises(ImproperlyConfigured, match="abstract model"):
        PackService().register(TimeStamped)


def test_register_rejects_duplicates():
    site = PackService()
    site.register(Author)

    with pytest.raises(ImproperlyConfigured, match="already registered"):
        site.register(Author)


@pytest.mark.parametrize("pack_cls", [object, "AuthorPack", ModelPack(Author)])
def test_register_requires_a_model_pack_subclass(pack_cls):
    with pytest.raises(ImproperlyConfigured, match="subclass of crudpack.ModelPack"):
        PackService().register(Author, pack_cls)


def test_register_decorator_returns_the_class_and_registers_it():
    site = PackService()

    @register("testapp.Author", site=site)
    class CustomPack(ModelPack):
        list_fields = ("name",)

    assert isinstance(site.get_pack(Author), CustomPack)
    assert CustomPack.__name__ == "CustomPack"


def test_urls_is_an_includable_triple():
    site = PackService(name="backoffice")
    site.register(Author)

    patterns, app_name, namespace = site.urls

    assert app_name == "packs"
    assert namespace == "backoffice"
    assert [str(p.pattern) for p in patterns] == ["testapp/author/"]
