class PackContextMixin:
    """Add the ``pack_info`` context shared by every view and pick the template."""

    pack = None
    pack_view = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opts = self.model._meta
        pack_info = context.setdefault("pack_info", {})
        pack_info.update(
            {
                "title": opts.verbose_name_plural,
                "app_name": opts.app_label,
                "model_name": opts.model_name,
                "paths": self.pack.get_paths(getattr(self, "object", None)),
            }
        )

        return context

    def get_template_names(self):
        template_name = self.pack.get_template_name(self.pack_view)

        if template_name:
            return [template_name]

        return super().get_template_names()


class SuccessUrlMixin:
    """Redirect to the pack's success URL after creating, updating or deleting."""

    def get_success_url(self):
        self.success_url = self.pack.get_success_url(self.pack_view, self.object)

        return super().get_success_url()
