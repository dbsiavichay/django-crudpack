from django.views.generic import DeleteView as BaseDeleteView
from django.views.generic import View

from viewpack.enums import PackViews

from .base import get_base_view


class DeleteMixin:
    name = PackViews.DELETE

    def get_success_url(self):
        self.success_url = self.pack.get_default_success_url()

        return super().get_success_url()


class DeleteView(View):
    pack = None

    def view(self, request, *args, **kwargs):
        mixins = [DeleteMixin]
        View = get_base_view(BaseDeleteView, mixins, self.pack)
        View.__bases__ = (*self.pack.delete_mixins, *View.__bases__)
        view = View.as_view()

        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
