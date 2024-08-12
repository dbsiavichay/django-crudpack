from django.views.generic import DetailView as BaseDetailView
from django.views.generic import View

from viewpack.enums import PackViews
from viewpack.services import FieldService

from .base import get_base_view


class DetailMixin:
    name = PackViews.DETAIL

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pack_info = context.get("pack_info", {})
        pack_info.update(self.get_fields_data())
        context["pack_info"] = pack_info

        return context

    def get_fields_data(self):
        service = FieldService(pack=self.pack)
        data, bs_data = service.get_detail_data(self.object)

        return {"fields": data, "bs_fieldsets": bs_data}


class DetailView(View):
    pack = None

    def view(self, request, *args, **kwargs):
        mixins = [DetailMixin]
        View = get_base_view(BaseDetailView, mixins, self.pack)
        View.__bases__ = (*self.pack.detail_mixins, *View.__bases__)
        view = View.as_view()

        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
