from django.apps import AppConfig


class ViewPackConfig(AppConfig):
    name = "viewpack"

    def ready(self):
        self.module.autodiscover()
