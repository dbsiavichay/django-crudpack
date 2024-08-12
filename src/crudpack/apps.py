from django.apps import AppConfig


class CrudPackConfig(AppConfig):
    name = "crudpack"

    def ready(self):
        self.module.autodiscover()
