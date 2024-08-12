from django.views.generic import CreateView as BaseCreateView
from django.views.generic import View

from viewpack.enums import PackViews
from viewpack.mixins import InlineMixin

from .base import get_base_view


class CreateMixin:
    name = PackViews.CREATE

    def get_success_url(self):
        self.success_url = self.pack.get_default_success_url()

        return super().get_success_url()


class CreateView(View):
    pack = None

    def view(self, request, *args, **kwargs):
        mixins = [CreateMixin]

        if self.pack.inlines:
            mixins.append(InlineMixin)

        View = get_base_view(BaseCreateView, mixins, self.pack)
        View.form_class = self.pack.form_class
        View.fields = self.pack.fields
        View.__bases__ = (*self.pack.form_mixins, *View.__bases__)
        view = View.as_view()

        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
