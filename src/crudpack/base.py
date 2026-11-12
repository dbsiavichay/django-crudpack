from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.db.models.base import ModelBase
from django.urls import path, reverse

from crudpack.enums import PackViews
from crudpack.services.fields import LOOKUP_SEP, FieldService
from crudpack.views import build_view

ALL_FIELDS = "__all__"

TEMPLATE_ATTRS = {
    PackViews.LIST: "list_template_name",
    PackViews.CREATE: "form_template_name",
    PackViews.UPDATE: "form_template_name",
    PackViews.DETAIL: "detail_template_name",
    PackViews.DELETE: "delete_template_name",
}

MIXINS_ATTRS = {
    PackViews.LIST: "list_mixins",
    PackViews.CREATE: "create_mixins",
    PackViews.UPDATE: "update_mixins",
    PackViews.DETAIL: "detail_mixins",
    PackViews.DELETE: "delete_mixins",
}


class ModelPack:
    """
    Declarative configuration for the CRUD views of a model.

    Subclass it, set the options below and register it with ``crudpack.register``
    or ``crudpack.packs.register``.
    """

    model = None

    # Forms (create and update views). With neither set, every field is editable.
    form_class = None
    fields = None
    # Formset classes (e.g. from inlineformset_factory) keyed by a unique name.
    inlines = {}

    # Field names shown on the list and detail views. Besides model fields they
    # accept methods, properties and "__"-separated paths (FKs and JSON keys).
    list_fields = ("__str__",)
    # A sequence of names/rows, or a dict of {fieldset title: rows}. When empty,
    # every concrete field of the model is shown.
    detail_fields = ()
    # Custom labels keyed by field name.
    default_labels = {}

    allowed_views = tuple(PackViews)
    # Where create, update and delete redirect to. Defaults to the list view.
    default_success_url = None

    # Templates. When unset, Django's defaults are used:
    # <app>/<model>_list.html, _form.html, _detail.html and _confirm_delete.html
    list_template_name = None
    form_template_name = None
    detail_template_name = None
    delete_template_name = None

    # Extra mixins for each view, placed before the crudpack and Django classes.
    list_mixins = ()
    create_mixins = ()
    update_mixins = ()
    detail_mixins = ()
    delete_mixins = ()

    # Custom queryset for every view. Defaults to the model's default manager.
    queryset = None
    paginate_by = None
    # Upper bound for the ``?paginate_by=`` query parameter.
    max_paginate_by = 100

    # Suffix of each URL name: "<namespace>:<app_label>_<model_name>_<suffix>"
    url_list_suffix = "list"
    url_create_suffix = "create"
    url_update_suffix = "update"
    url_detail_suffix = "detail"
    url_delete_suffix = "delete"

    # URL namespace, set by the PackService that registers the pack.
    namespace = "packs"

    def __init__(self, model=None, **options):
        if model is not None:
            self.model = model

        for key, value in options.items():
            if not hasattr(type(self), key) or key.startswith("_"):
                raise ImproperlyConfigured(
                    f"{type(self).__name__} received an invalid option {key!r}."
                )
            setattr(self, key, value)

        self._validate()

    # Validation

    def _validate(self):
        if not isinstance(self.model, ModelBase):
            raise ImproperlyConfigured(
                f"{type(self).__name__} requires a Django model, got {self.model!r}."
            )

        self.allowed_views = self._validate_allowed_views(self.allowed_views)

        for attr in ("list_fields", "detail_fields"):
            value = getattr(self, attr)
            if isinstance(value, str) or not isinstance(value, (list, tuple, dict)):
                raise ImproperlyConfigured(
                    f"The {attr!r} option must be a list, tuple or dict."
                )

        if isinstance(self.list_fields, dict):
            raise ImproperlyConfigured("The 'list_fields' option cannot be a dict.")

        self.list_fields = tuple(self.list_fields)
        if not self.list_fields:
            raise ImproperlyConfigured("The 'list_fields' option cannot be empty.")

        if not self.detail_fields:
            self.detail_fields = tuple(field.name for field in self.model._meta.fields)

        names = self.list_fields + tuple(
            FieldService.get_flatten_field_names(self.detail_fields)
        )
        for name in names:
            self._validate_field_name(name)

        for attr in ("default_labels", "inlines"):
            if not isinstance(getattr(self, attr), dict):
                raise ImproperlyConfigured(f"The {attr!r} option must be a dict.")

        for attr in MIXINS_ATTRS.values():
            if not isinstance(getattr(self, attr), (list, tuple)):
                raise ImproperlyConfigured(f"The {attr!r} option must be a tuple.")

        if self.form_class and self.fields:
            raise ImproperlyConfigured("Set either 'form_class' or 'fields', not both.")

        if not self.form_class and not self.fields:
            self.fields = ALL_FIELDS

        if self.queryset is not None and not isinstance(self.queryset, models.QuerySet):
            raise ImproperlyConfigured("The 'queryset' option must be a QuerySet.")

        for attr in ("paginate_by", "max_paginate_by"):
            value = getattr(self, attr)
            if value is not None and (not isinstance(value, int) or value < 1):
                raise ImproperlyConfigured(
                    f"The {attr!r} option must be a positive integer."
                )

        self._validate_success_url()

    def _validate_allowed_views(self, allowed_views):
        if not isinstance(allowed_views, (list, tuple)) or not allowed_views:
            raise ImproperlyConfigured(
                "The 'allowed_views' option must be a non-empty list or tuple."
            )

        if not all(isinstance(view, PackViews) for view in allowed_views):
            raise ImproperlyConfigured(
                "The 'allowed_views' items must be PackViews members."
            )

        return tuple(dict.fromkeys(allowed_views))

    def _validate_field_name(self, name):
        if not isinstance(name, str):
            raise ImproperlyConfigured(f"Field names must be strings, got {name!r}.")

        if name == "__str__":
            return

        root = name.split(LOOKUP_SEP)[0]

        try:
            self.model._meta.get_field(root)
        except FieldDoesNotExist:
            if not hasattr(self.model, root):
                raise ImproperlyConfigured(
                    f"{self.model.__name__} has no field, method or property "
                    f"named {root!r} (used in {type(self).__name__})."
                ) from None

    def _validate_success_url(self):
        if self.default_success_url or PackViews.LIST in self.allowed_views:
            return

        if PackViews.DELETE in self.allowed_views:
            raise ImproperlyConfigured(
                "The delete view needs the list view or 'default_success_url' "
                "to redirect after deleting."
            )

        writes = {PackViews.CREATE, PackViews.UPDATE} & set(self.allowed_views)
        if writes and PackViews.DETAIL not in self.allowed_views:
            raise ImproperlyConfigured(
                "The create and update views need the list view, the detail view "
                "or 'default_success_url' to redirect after saving."
            )

    # Views

    @property
    def model_info(self):
        return self.model._meta.app_label, self.model._meta.model_name

    def get_template_name(self, view):
        return getattr(self, TEMPLATE_ATTRS[view])

    def get_mixins(self, view):
        return tuple(getattr(self, MIXINS_ATTRS[view]))

    def post_save_inlines(self, instance):
        """Hook called after the object and its inlines are saved."""

    # URLs

    def get_base_url_name(self, view):
        view = PackViews(view)
        suffix = getattr(self, f"url_{view.value}_suffix")
        return "{}_{}_{}".format(*self.model_info, suffix)

    def get_url_name(self, view):
        return f"{self.namespace}:{self.get_base_url_name(view)}"

    def get_pk_converter(self):
        pk = self.model._meta.pk

        while pk.is_relation:
            pk = pk.target_field

        if isinstance(pk, models.UUIDField):
            return "uuid"

        if isinstance(pk, models.IntegerField):
            return "int"

        return "str"

    def get_route(self, view):
        if view is PackViews.LIST:
            return ""

        if view.is_object_view:
            return f"<{self.get_pk_converter()}:pk>/{view.value}/"

        return f"{view.value}/"

    def get_urls(self):
        return [
            path(
                self.get_route(view),
                build_view(self, view).as_view(),
                name=self.get_base_url_name(view),
            )
            for view in self.allowed_views
        ]

    @property
    def urls(self):
        return self.get_urls()

    def get_paths(self, instance=None):
        """
        Return the URL of every allowed view keyed by view name.

        URLs of single-object views are only included when ``instance`` is given.
        """
        paths = {}

        for view in self.allowed_views:
            if view.is_object_view:
                if instance is None or instance.pk is None:
                    continue
                kwargs = {"pk": instance.pk}
            else:
                kwargs = {}

            paths[view.value] = reverse(self.get_url_name(view), kwargs=kwargs)

        return paths

    @property
    def paths(self):
        return self.get_paths()

    def get_success_url(self, view, instance=None):
        """Where ``view`` (create, update or delete) redirects after success."""
        if self.default_success_url:
            return str(self.default_success_url)

        if PackViews.LIST in self.allowed_views:
            return reverse(self.get_url_name(PackViews.LIST))

        if view is not PackViews.DELETE and PackViews.DETAIL in self.allowed_views:
            return reverse(
                self.get_url_name(PackViews.DETAIL), kwargs={"pk": instance.pk}
            )

        # Unreachable for a validated pack: _validate_success_url() checks it.
        raise ImproperlyConfigured(  # pragma: no cover
            f"No success URL for the {view.value} view."
        )
