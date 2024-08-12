from django.shortcuts import redirect


class Inline:
    instance = None

    def __init__(self, formset):
        self.formset = formset
        self.headers = [field.label for field in formset.form.base_fields.values()]

    def is_valid(self):
        return self.formset.is_valid()

    def save(self):
        self.formset.instance = self.instance
        self.formset.save()

    @property
    def errors(self):
        return self.formset.errors


class InlineMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inlines = self.get_inlines()

        if inlines:
            pack_info = context.get("pack_info", {})
            pack_info.update({"inlines": inlines})
            context["pack_info"] = pack_info

        return context

    def get_inlines(self):
        kwargs = self.get_form_kwargs()

        return {
            name: Inline(inline_class(**kwargs))
            for name, inline_class in self.pack.inlines.items()
        }

    def form_valid(self, form):
        inlines = self.get_inlines().values()

        if any([not inline.is_valid() for inline in inlines]):
            form.inlines = inlines
            return self.form_invalid(form)

        self.object = form.save()

        for inline in inlines:
            inline.instance = self.object
            inline.save()

        self.pack.post_save_inlines(self.object)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        inlines = getattr(form, "inlines", [])

        for inline in inlines:
            for error in inline.errors:
                form.errors.update(error)

        return super().form_invalid(form)
