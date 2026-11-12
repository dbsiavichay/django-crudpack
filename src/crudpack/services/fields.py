from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.db.models.manager import BaseManager
from django.forms.utils import pretty_name

LOOKUP_SEP = "__"
STR_FIELD = "__str__"


def flatten(items):
    """Flatten one level of nesting: ``("a", ("b", "c"))`` -> ``["a", "b", "c"]``."""
    if isinstance(items, str):
        return [items]

    result = []

    for item in items:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)

    return result


class FieldService:
    """Resolve labels and values of the fields shown by the list and detail views."""

    def __init__(self, pack):
        self.pack = pack

    @staticmethod
    def get_flatten_field_names(field_names):
        if isinstance(field_names, dict):
            return [name for rows in field_names.values() for name in flatten(rows)]

        return flatten(field_names)

    @staticmethod
    def get_bootstrap_fields(rows, fields_data):
        """Group ``fields_data`` in rows, adding the Bootstrap column width."""
        if isinstance(rows, str):
            rows = (rows,)

        result = []

        for row in rows:
            row = row if isinstance(row, (list, tuple)) else (row,)
            cols = 12 // len(row)
            result.append({name: {**fields_data[name], "cols": cols} for name in row})

        return result

    def get_field_label(self, field_name):
        labels = self.pack.default_labels

        if field_name in labels:
            return labels[field_name]

        model = self.pack.model

        if field_name == STR_FIELD:
            return pretty_name(model._meta.verbose_name)

        names = field_name.split(LOOKUP_SEP)

        if len(names) == 1:
            try:
                return pretty_name(model._meta.get_field(field_name).verbose_name)
            except (FieldDoesNotExist, AttributeError):
                pass

        return pretty_name(names[-1])

    def get_field_data(self, obj, field_name):
        if field_name == STR_FIELD:
            value, field_type = obj, type(obj).__name__.lower()
        else:
            value, field_type = self._resolve(obj, field_name.split(LOOKUP_SEP))

        return {
            "value": value,
            "label": self.get_field_label(field_name),
            "type": field_type,
        }

    def _resolve(self, obj, names):
        name, *rest = names
        field = None

        if isinstance(obj, dict):
            value = obj.get(name)
        else:
            if not hasattr(obj, name):
                raise AttributeError(
                    f"{type(obj).__name__} has no attribute {name!r} ({obj!r})."
                )

            if isinstance(obj, Model):
                try:
                    field = obj._meta.get_field(name)
                except FieldDoesNotExist:
                    field = None

            if field is not None and getattr(field, "choices", None) and not rest:
                value = getattr(obj, f"get_{field.name}_display")()
            else:
                value = getattr(obj, name)

                if callable(value) and not isinstance(value, BaseManager):
                    value = value()

        if rest:
            if value is None:
                return None, "nonetype"

            return self._resolve(value, rest)

        if isinstance(value, FieldFile):
            value = {"name": value.name, "url": value.url} if value else None

        field_type = field.get_internal_type() if field else type(value).__name__

        return value, field_type.lower()

    def _get_data(self, instances, field_names):
        return [
            (
                instance,
                {name: self.get_field_data(instance, name) for name in field_names},
            )
            for instance in instances
        ]

    def get_list_data(self, instances):
        return self._get_data(instances, self.pack.list_fields)

    def get_detail_data(self, instance):
        detail_fields = self.pack.detail_fields
        field_names = self.get_flatten_field_names(detail_fields)
        _, data = self._get_data([instance], field_names)[0]

        fieldsets = (
            detail_fields.items()
            if isinstance(detail_fields, dict)
            else [("", detail_fields)]
        )

        bs_data = [
            {"title": title, "fieldset": self.get_bootstrap_fields(rows, data)}
            for title, rows in fieldsets
        ]

        return data, bs_data
