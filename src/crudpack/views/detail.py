from crudpack.services import FieldService


class DetailMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pack_info = context.setdefault("pack_info", {})
        pack_info.update(self.get_fields_data())

        return context

    def get_fields_data(self):
        service = FieldService(self.pack)
        data, bs_data = service.get_detail_data(self.object)

        return {"fields": data, "bs_fieldsets": bs_data}
