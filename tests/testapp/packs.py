from django.contrib.auth.mixins import LoginRequiredMixin

from crudpack import ModelPack, PackViews, register

from .forms import BookForm, BookFormSet
from .models import Author, Publisher, Tag


class ExtraContextMixin:
    """A user mixin: runs after crudpack filled ``pack_info``."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extra"] = sorted(context["pack_info"])
        return context


class GenericTemplatesPack(ModelPack):
    list_template_name = "crud/list.html"
    form_template_name = "crud/form.html"
    detail_template_name = "crud/detail.html"
    delete_template_name = "crud/confirm_delete.html"


@register(Author)
class AuthorPack(ModelPack):
    # Uses Django's default template names: testapp/author_<suffix>.html
    list_fields = ("name", "email", "shout", "initials", "book_count", "bold_name")
    detail_fields = {"Main": (("name", "email"),), "Extra": ("shout",)}
    default_labels = {"email": "E-mail address"}
    inlines = {"books": BookFormSet}
    paginate_by = 2
    max_paginate_by = 3


@register("testapp.Book")
class BookPack(GenericTemplatesPack):
    form_class = BookForm
    list_fields = (
        "__str__",
        "author",
        "author__name",
        "status",
        "cover",
        "metadata__color",
        "pages",
    )
    detail_fields = ("title", ("status", "pages"), "cover")


@register(Tag)
class TagPack(GenericTemplatesPack):
    fields = ("name",)
    list_mixins = (ExtraContextMixin,)
    delete_mixins = (LoginRequiredMixin,)


@register(Publisher)
class PublisherPack(GenericTemplatesPack):
    # No list view: create and update must redirect to the detail view.
    allowed_views = (PackViews.CREATE, PackViews.UPDATE, PackViews.DETAIL)
    fields = ("code", "name")
