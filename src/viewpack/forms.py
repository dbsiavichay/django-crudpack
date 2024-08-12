from functools import cached_property

from django.core.exceptions import ImproperlyConfigured
from django.forms import BaseModelForm
from django.forms.models import ModelFormMetaclass as DjangoModelFormMetaclass

from viewpack.services import FieldService


class ModelFormMetaclass(DjangoModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        metadata = attrs.get("Meta")
        fieldsets = getattr(metadata, "fieldsets", None)

        if fieldsets:
            field_names = mcs.__fields__(fieldsets)
            fields = getattr(metadata, "fields", ())

            if isinstance(fields, (tuple, list)):
                fields = fields + field_names

            metadata.fields = fields

        new_class = super().__new__(mcs, name, bases, attrs)

        if fieldsets:
            new_class._meta.fieldsets = fieldsets

        return new_class

    def __fields__(field_names):
        if not isinstance(field_names, (tuple, list, dict)):
            raise ImproperlyConfigured(
                "The fieldsets must be an instance of list, tuple or dict"
            )

        fields = FieldService.get_flatten_field_names(field_names)

        return tuple(fields)


class ModelForm(BaseModelForm, metaclass=ModelFormMetaclass):
    def parse(self, field_names):
        def wrap(fields):
            fields = fields if isinstance(fields, (list, tuple)) else (fields,)
            cols = int(12 / len(fields))

            return [(self[field], cols) for field in fields]

        data = list(map(wrap, field_names))

        return data

    @cached_property
    def bs_fieldsets(self):
        field_names = getattr(self._meta, "fieldsets", self.fields.keys())
        fieldsets = (
            field_names.items()
            if isinstance(field_names, dict)
            else [("", field_names)]
        )
        data = [
            {"title": title, "fieldset": self.parse(fieldset)}
            for title, fieldset in fieldsets
        ]

        return data
