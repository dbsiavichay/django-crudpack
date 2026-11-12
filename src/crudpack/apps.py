from django.apps import AppConfig


class CrudPackConfig(AppConfig):
    name = "crudpack"
    verbose_name = "CRUD pack"

    def ready(self):
        self.module.autodiscover()
