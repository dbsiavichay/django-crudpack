from django.views.generic import ListView as BaseListView
from django.views.generic import View

from viewpack.enums import PackViews
from viewpack.services import FieldService

from .base import get_base_view


class ListMixin:
    name = PackViews.LIST

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pack_info = context.get("pack_info", {})
        object_list = context.get("object_list")
        object_list_count = object_list.count()
        is_paginated = context.get("is_paginated")
        paginator = context.get("paginator")
        page_obj = context.get("page_obj")
        start_index = page_obj.start_index() if is_paginated else 1
        end_index = page_obj.end_index() if is_paginated else object_list_count
        count = paginator.count if is_paginated else object_list_count
        pack_info.update(
            {
                **self.get_fields_data(object_list),
                "start_index": start_index,
                "end_index": end_index,
                "count": count,
            }
        )
        context["pack_info"] = pack_info

        return context

    def get_fields_data(self, queryset):
        service = FieldService(self.pack)
        data = service.get_list_data(queryset)

        return {
            "headers": {
                name: service._get_field_label(name) for name in self.pack.list_fields
            },
            "rows": self.get_rows(data),
        }

    def get_rows(self, data):
        return [
            (instance, {"data": row, "paths": self.pack.get_paths(instance)})
            for instance, row in data
        ]

    def get_paginate_by(self, queryset):
        paginate_by = self.request.GET.get("paginate_by")

        if paginate_by:
            return paginate_by

        return super().get_paginate_by(queryset)


class ListView(View):
    pack = None

    def view(self, request, *args, **kwargs):
        mixins = [ListMixin]
        View = get_base_view(BaseListView, mixins, self.pack)
        View.paginate_by = self.pack.paginate_by
        View.__bases__ = (*self.pack.list_mixins, *View.__bases__)
        view = View.as_view()

        return view(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
