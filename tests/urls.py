from django.urls import path

from crudpack import packs

# Mounted under a prefix on purpose: every generated URL must include it.
urlpatterns = [path("crud/", packs.urls)]
