import pytest
from django.urls import NoReverseMatch, path, reverse

from crudpack import PackService, packs
from tests.testapp.models import Author, Publisher, Tag

backoffice = PackService(name="backoffice")
backoffice.register(Author)

# URLconf used by the tests marked with @pytest.mark.urls(__name__)
urlpatterns = [path("admin/crud/", backoffice.urls)]


def test_urls_are_mounted_under_the_prefix():
    assert reverse("packs:testapp_author_list") == "/crud/testapp/author/"
    assert reverse("packs:testapp_author_create") == "/crud/testapp/author/create/"
    assert reverse("packs:testapp_author_detail", kwargs={"pk": 7}) == (
        "/crud/testapp/author/7/detail/"
    )


def test_paths_without_instance_only_have_collection_views():
    assert packs.get_pack(Author).paths == {
        "list": "/crud/testapp/author/",
        "create": "/crud/testapp/author/create/",
    }


def test_paths_with_instance(author):
    assert packs.get_pack(Author).get_paths(author) == {
        "list": "/crud/testapp/author/",
        "create": "/crud/testapp/author/create/",
        "update": f"/crud/testapp/author/{author.pk}/update/",
        "detail": f"/crud/testapp/author/{author.pk}/detail/",
        "delete": f"/crud/testapp/author/{author.pk}/delete/",
    }


def test_paths_of_unsaved_instance_skip_object_views():
    assert set(packs.get_pack(Author).get_paths(Author(name="x"))) == {
        "list",
        "create",
    }


def test_uuid_primary_key(client, tag):
    url = f"/crud/testapp/tag/{tag.pk}/detail/"

    assert packs.get_pack(Tag).get_paths(tag)["detail"] == url
    assert client.get(url).status_code == 200


def test_string_primary_key(client, publisher):
    url = "/crud/testapp/publisher/acme/detail/"

    assert packs.get_pack(Publisher).get_paths(publisher) == {
        "create": "/crud/testapp/publisher/create/",
        "update": "/crud/testapp/publisher/acme/update/",
        "detail": url,
    }
    assert client.get(url).status_code == 200


def test_views_not_allowed_have_no_url(client, publisher):
    with pytest.raises(NoReverseMatch):
        reverse("packs:testapp_publisher_list")

    assert client.get("/crud/testapp/publisher/").status_code == 404
    assert client.get("/crud/testapp/publisher/acme/delete/").status_code == 404


@pytest.mark.urls(__name__)
def test_custom_service_namespace_and_prefix(client, author):
    pack = backoffice.get_pack(Author)

    assert pack.get_paths(author)["detail"] == (
        f"/admin/crud/testapp/author/{author.pk}/detail/"
    )

    response = client.get("/admin/crud/testapp/author/")

    assert response.status_code == 200
    assert response.context["pack_info"]["paths"]["create"] == (
        "/admin/crud/testapp/author/create/"
    )
