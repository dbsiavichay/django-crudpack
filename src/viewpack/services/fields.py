from functools import reduce

from django.contrib.admin.utils import flatten
from django.core.exceptions import FieldDoesNotExist
from django.db.models.base import ModelBase
from django.forms.utils import pretty_name
from django.utils.html import format_html


class FieldService:
    JSON_SPLITTER = "__"

    pack = None

    def __init__(self, pack):
        self.pack = pack

    @classmethod
    def get_flatten_field_names(cls, field_names):
        if isinstance(field_names, dict):
            field_names = reduce(
                lambda accumulator, names: accumulator + flatten(names),
                field_names.values(),
                [],
            )
        else:
            field_names = flatten(field_names)

        return field_names

    @classmethod
    def get_botstrap_fields(cls, field_names, fields_data):
        def wrap(fields):
            fields = fields if isinstance(fields, (list, tuple)) else (fields,)
            cols = int(12 / len(fields))
            result = {field: fields_data.get(field) for field in fields}

            for value in result.values():
                value.update({"cols": cols})

            return result

        data = list(map(wrap, field_names))

        return data

    def _get_field_label(self, field_name):
        label = self.pack.default_labels.get(field_name)

        if label:
            return pretty_name(label)

        if "__str__" in field_name:
            label = self.pack.model._meta.verbose_name
            return pretty_name(label)

        names = field_name.split(self.JSON_SPLITTER)
        name = names.pop(0)

        try:
            field = self.pack.model._meta.get_field(name)
            label = field.verbose_name
        except FieldDoesNotExist:
            label = field_name

        return pretty_name(label)

    def _get_field_data(self, obj, large_field_name, field_name):
        if "__str__" == field_name:
            return {
                "value": obj,
                "label": self._get_field_label(large_field_name),
                "type": type(obj).__name__,
            }

        names = field_name.split(self.JSON_SPLITTER)
        name = names.pop(0)
        has_attr = name in obj if isinstance(obj, dict) else hasattr(obj, name)

        if not has_attr:
            raise AttributeError(
                "Does not exist attribute <{0}> for {1}".format(field_name, str(obj))
            )

        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        value = value() if callable(value) else value
        is_file = hasattr(value, "field") and value.field.get_internal_type() in [
            "FileField",
            "ImageField",
        ]

        if is_file:
            value = {"name": value.name, "url": value.url} if bool(value) else None

        if len(names) and isinstance(value, dict):
            return self._get_field_data(
                value, large_field_name, self.JSON_SPLITTER.join(names)
            )

        try:
            field = obj._meta.get_field(name)
            internal_type = field.get_internal_type()

            if hasattr(field, "choices") and field.choices:
                value = dict(field.choices).get(value)
        except (FieldDoesNotExist, AttributeError):
            value = format_html(value)
            internal_type = type(value).__name__

        label = self._get_field_label(large_field_name)
        internal_type = internal_type.lower()

        return {"value": value, "label": label, "type": internal_type}

    def _get_data(self, instance_or_queryset, field_names):
        if isinstance(type(instance_or_queryset), ModelBase):
            instance_or_queryset = [instance_or_queryset]

        data = [
            (
                instance,
                {
                    field_name: self._get_field_data(instance, field_name, field_name)
                    for field_name in field_names
                },
            )
            for instance in instance_or_queryset
        ]

        return data

    def get_list_data(self, instance_or_queryset):
        return self._get_data(instance_or_queryset, self.pack.list_fields)

    def get_detail_data(self, instance_or_queryset):
        field_names = self.get_flatten_field_names(self.pack.detail_fields)
        data = self._get_data(instance_or_queryset, field_names) or {}

        if len(data):
            _, data = data[0]

        field_names = self.pack.detail_fields

        if not field_names:
            field_names = data.keys()

        fieldsets = (
            field_names.items()
            if isinstance(field_names, dict)
            else [("", field_names)]
        )

        bs_data = [
            {
                "title": title,
                "fieldset": self.get_botstrap_fields(
                    fieldset,
                    data,
                ),
            }
            for title, fieldset in fieldsets
        ]

        return data, bs_data
