from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.urls import include, path


class PackService:
    def __init__(self, name="packs"):
        self._registry = {}
        self.name = name

    def register(self, model, pack_cls):
        if isinstance(model, str):
            try:
                app_label, model_name = model.split(".")
                model = apps.get_model(app_label, model_name)
            except ValueError:
                raise ImproperlyConfigured(
                    "The model_name passed"
                    "must be contains app label and model name"
                    "like 'app_label.model_name'"
                )

        if not isinstance(model, ModelBase):
            raise ImproperlyConfigured(
                "The model passed cannot be registered.",
            )

        if model._meta.abstract:
            raise ImproperlyConfigured(
                "The abstract model %s cannot be registered." % model.__name__
            )

        if model in self._registry:
            raise ImproperlyConfigured(
                "The model %s is already registered" % model.__name__
            )

        self._registry[model] = pack_cls(model)

    def is_registered(self, model):
        return model in self._registry

    def get_default_urls(self):
        urlpatterns = []

        for pack in self._registry.values():
            urlpatterns += [
                path(
                    "%s/%s/" % pack.model_info,
                    include(pack.urls),
                ),
            ]

        return urlpatterns

    @property
    def urls(self):
        return self.get_default_urls(), "packs", self.name


packs = PackService()
