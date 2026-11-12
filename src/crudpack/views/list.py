from crudpack.services import FieldService


class ListMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_list = context["object_list"]
        page_obj = context.get("page_obj")

        if page_obj is not None:
            start_index = page_obj.start_index()
            end_index = page_obj.end_index()
            count = page_obj.paginator.count
        else:
            count = len(object_list)
            start_index = 1 if count else 0
            end_index = count

        pack_info = context.setdefault("pack_info", {})
        pack_info.update(
            {
                **self.get_fields_data(object_list),
                "start_index": start_index,
                "end_index": end_index,
                "count": count,
            }
        )

        return context

    def get_fields_data(self, object_list):
        service = FieldService(self.pack)
        data = service.get_list_data(object_list)

        return {
            "headers": {
                name: service.get_field_label(name) for name in self.pack.list_fields
            },
            "rows": self.get_rows(data),
        }

    def get_rows(self, data):
        return [
            (instance, {"data": row, "paths": self.pack.get_paths(instance)})
            for instance, row in data
        ]

    def get_paginate_by(self, queryset):
        paginate_by = super().get_paginate_by(queryset)

        try:
            requested = int(self.request.GET["paginate_by"])
        except (KeyError, ValueError):
            return paginate_by

        if requested < 1:
            return paginate_by

        return min(requested, self.pack.max_paginate_by)
