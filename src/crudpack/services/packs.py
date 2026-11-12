from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.urls import include, path

from crudpack.base import ModelPack


def resolve_model(model):
    """Return the model class for a model class or an ``"app_label.Model"`` string."""
    if isinstance(model, str):
        try:
            return apps.get_model(model)
        except (LookupError, ValueError) as error:
            raise ImproperlyConfigured(
                f"Cannot resolve model {model!r}. Use the 'app_label.ModelName' "
                f"format with an installed model: {error}"
            ) from error

    if not isinstance(model, ModelBase):
        raise ImproperlyConfigured(
            f"{model!r} is not a Django model and cannot be registered."
        )

    return model


class PackService:
    """Registry of ``ModelPack`` instances, mounted in the URLconf like the admin."""

    app_name = "packs"

    def __init__(self, name="packs"):
        self._registry = {}
        self.name = name

    def register(self, model, pack_cls=None):
        model = resolve_model(model)
        pack_cls = pack_cls or ModelPack

        if not (isinstance(pack_cls, type) and issubclass(pack_cls, ModelPack)):
            raise ImproperlyConfigured(
                f"{pack_cls!r} must be a subclass of crudpack.ModelPack."
            )

        if model._meta.abstract:
            raise ImproperlyConfigured(
                f"The abstract model {model.__name__} cannot be registered."
            )

        if model in self._registry:
            raise ImproperlyConfigured(
                f"The model {model.__name__} is already registered."
            )

        pack = pack_cls(model, namespace=self.name)
        self._registry[model] = pack

        return pack

    def is_registered(self, model):
        return resolve_model(model) in self._registry

    def get_pack(self, model):
        return self._registry[resolve_model(model)]

    def get_urls(self):
        return [
            path("{}/{}/".format(*pack.model_info), include(pack.urls))
            for pack in self._registry.values()
        ]

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name


packs = PackService()
