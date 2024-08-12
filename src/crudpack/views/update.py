from django.views.generic import UpdateView as BaseUpdateView
from django.views.generic import View

from crudpack.enums import PackViews
from crudpack.mixins import InlineMixin

from .base import get_base_view


class UpdateMixin:
    name = PackViews.UPDATE

    def get_success_url(self):
        self.success_url = self.pack.get_default_success_url()

        return super().get_success_url()


class UpdateView(View):
    pack = None

    def view(self, request, *args, **kwargs):
        mixins = [UpdateMixin]

        if self.pack.inlines:
            mixins.append(InlineMixin)

        View = get_base_view(BaseUpdateView, mixins, self.pack)
        View.form_class = self.pack.form_class
        View.fields = self.pack.fields
        View.__bases__ = (*self.pack.update_mixins, *View.__bases__)
        view = View.as_view()

        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
