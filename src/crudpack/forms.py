from functools import cached_property

from django.core.exceptions import ImproperlyConfigured
from django.forms import BaseModelForm
from django.forms.models import ModelFormMetaclass as DjangoModelFormMetaclass

from crudpack.services import FieldService


class ModelFormMetaclass(DjangoModelFormMetaclass):
    """
    Accept ``Meta.fieldsets``: a sequence of rows, or a dict of {title: rows}.

    Every field named in the fieldsets is added to ``Meta.fields``.
    """

    def __new__(mcs, name, bases, attrs):
        meta = attrs.get("Meta")
        fieldsets = getattr(meta, "fieldsets", None)

        if fieldsets:
            field_names = mcs._flatten_fieldsets(fieldsets)
            fields = getattr(meta, "fields", None)

            if fields is None:
                meta.fields = field_names
            elif isinstance(fields, (list, tuple)):
                fields = tuple(fields)
                meta.fields = fields + tuple(
                    name for name in field_names if name not in fields
                )

        new_class = super().__new__(mcs, name, bases, attrs)
        inherited_meta = getattr(new_class, "Meta", None)
        fieldsets = getattr(inherited_meta, "fieldsets", None)

        if fieldsets:
            new_class._meta.fieldsets = fieldsets

        return new_class

    @staticmethod
    def _flatten_fieldsets(fieldsets):
        if isinstance(fieldsets, str) or not isinstance(fieldsets, (tuple, list, dict)):
            raise ImproperlyConfigured(
                "The fieldsets must be an instance of list, tuple or dict"
            )

        return tuple(dict.fromkeys(FieldService.get_flatten_field_names(fieldsets)))


class ModelForm(BaseModelForm, metaclass=ModelFormMetaclass):
    """A ``ModelForm`` that exposes its fields grouped in Bootstrap rows."""

    def parse(self, rows):
        if isinstance(rows, str):
            rows = (rows,)

        data = []

        for row in rows:
            row = row if isinstance(row, (list, tuple)) else (row,)
            cols = 12 // len(row)
            data.append([(self[name], cols) for name in row])

        return data

    @cached_property
    def bs_fieldsets(self):
        fieldsets = getattr(self._meta, "fieldsets", None) or tuple(self.fields)
        groups = fieldsets.items() if isinstance(fieldsets, dict) else [("", fieldsets)]

        return [
            {"title": title, "fieldset": self.parse(rows)} for title, rows in groups
        ]
