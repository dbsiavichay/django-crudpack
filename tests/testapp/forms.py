from django import forms

from crudpack.forms import ModelForm

from .models import Author, Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        # A list on purpose: it used to raise TypeError when merged with fieldsets.
        fields = ["title"]
        fieldsets = {
            "General": ("title", ("author", "status")),
            "Details": ("pages", "metadata"),
        }


BookFormSet = forms.inlineformset_factory(
    Author, Book, fields=("title", "pages"), extra=1, can_delete=False
)
