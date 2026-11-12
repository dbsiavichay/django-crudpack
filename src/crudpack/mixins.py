from django.db import transaction
from django.http import HttpResponseRedirect


class Inline:
    """A formset of the create/update views, with what templates need to render it."""

    def __init__(self, name, formset):
        self.name = name
        self.formset = formset
        self.headers = [field.label for field in formset.form.base_fields.values()]

    def is_valid(self):
        return self.formset.is_valid()

    def save(self, instance):
        self.formset.instance = instance
        return self.formset.save()

    @property
    def errors(self):
        return self.formset.errors

    @property
    def non_form_errors(self):
        return self.formset.non_form_errors()


class InlineMixin:
    """Render, validate and save the pack's ``inlines`` together with the form."""

    _inlines = None

    def get_inline_kwargs(self, name, instance):
        kwargs = {"instance": instance, "prefix": name}

        if self.request.method in ("POST", "PUT"):
            kwargs.update({"data": self.request.POST, "files": self.request.FILES})

        return kwargs

    def get_inlines(self, instance=None):
        if self._inlines is None:
            instance = instance if instance is not None else self.object
            self._inlines = {
                name: Inline(
                    name, formset_class(**self.get_inline_kwargs(name, instance))
                )
                for name, formset_class in self.pack.inlines.items()
            }

        return self._inlines

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("pack_info", {})["inlines"] = self.get_inlines()

        return context

    def form_valid(self, form):
        inlines = self.get_inlines(instance=form.instance).values()
        # Validate every inline (no short-circuit) so all their errors are shown.
        if not all([inline.is_valid() for inline in inlines]):
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()

            for inline in inlines:
                inline.save(self.object)

            self.pack.post_save_inlines(self.object)

        return HttpResponseRedirect(self.get_success_url())
