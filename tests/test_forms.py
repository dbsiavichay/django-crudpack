import pytest
from django.core.exceptions import ImproperlyConfigured

from crudpack.forms import ModelForm
from tests.testapp.forms import BookForm
from tests.testapp.models import Book, Tag


def names(fieldset):
    return [[(bound.name, cols) for bound, cols in row] for row in fieldset]


def test_fieldsets_are_merged_into_a_list_of_fields():
    assert BookForm._meta.fields == ("title", "author", "status", "pages", "metadata")
    assert list(BookForm().fields) == ["title", "author", "status", "pages", "metadata"]


def test_bs_fieldsets_from_dict():
    fieldsets = BookForm().bs_fieldsets

    assert [fieldset["title"] for fieldset in fieldsets] == ["General", "Details"]
    assert names(fieldsets[0]["fieldset"]) == [
        [("title", 12)],
        [("author", 6), ("status", 6)],
    ]
    assert names(fieldsets[1]["fieldset"]) == [[("pages", 12)], [("metadata", 12)]]


def test_fieldsets_without_fields():
    class TagForm(ModelForm):
        class Meta:
            model = Tag
            fieldsets = (("name",),)

    form = TagForm()

    assert list(form.fields) == ["name"]
    assert names(form.bs_fieldsets[0]["fieldset"]) == [[("name", 12)]]


def test_fieldsets_with_all_fields():
    class AllBookForm(ModelForm):
        class Meta:
            model = Book
            fields = "__all__"
            fieldsets = ("title",)

    form = AllBookForm()

    assert {"title", "author", "status", "pages", "metadata"} <= set(form.fields)
    assert names(form.bs_fieldsets[0]["fieldset"]) == [[("title", 12)]]


def test_fieldset_group_can_be_a_single_name():
    class TagForm(ModelForm):
        class Meta:
            model = Tag
            fieldsets = {"Main": "name"}

    assert names(TagForm().bs_fieldsets[0]["fieldset"]) == [[("name", 12)]]


def test_form_without_fieldsets():
    class TagForm(ModelForm):
        class Meta:
            model = Tag
            fields = ("name",)

    assert TagForm().bs_fieldsets[0]["title"] == ""
    assert names(TagForm().bs_fieldsets[0]["fieldset"]) == [[("name", 12)]]


def test_subclasses_inherit_fieldsets():
    class ChildForm(BookForm):
        pass

    assert ChildForm._meta.fieldsets == BookForm._meta.fieldsets
    assert len(ChildForm().bs_fieldsets) == 2


def test_invalid_fieldsets():
    with pytest.raises(ImproperlyConfigured, match="fieldsets must be"):

        class TagForm(ModelForm):
            class Meta:
                model = Tag
                fieldsets = "name"
