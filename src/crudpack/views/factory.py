from django.views import generic

from crudpack.enums import PackViews
from crudpack.mixins import InlineMixin

from .base import PackContextMixin
from .create import CreateMixin
from .delete import DeleteMixin
from .detail import DetailMixin
from .list import ListMixin
from .update import UpdateMixin

VIEW_CLASSES = {
    PackViews.LIST: (ListMixin, generic.ListView),
    PackViews.CREATE: (CreateMixin, generic.CreateView),
    PackViews.UPDATE: (UpdateMixin, generic.UpdateView),
    PackViews.DETAIL: (DetailMixin, generic.DetailView),
    PackViews.DELETE: (DeleteMixin, generic.DeleteView),
}


def build_view(pack, view):
    """
    Build the class-based view for ``view`` of ``pack``.

    The MRO is: the pack's mixins for that view, ``PackContextMixin``, the crudpack
    mixin of the view (plus ``InlineMixin`` on forms with inlines) and finally the
    Django generic view.
    """
    view_mixin, generic_view = VIEW_CLASSES[view]
    bases = [*pack.get_mixins(view), PackContextMixin, view_mixin]
    attrs = {
        "__module__": __name__,
        "pack": pack,
        "pack_view": view,
        "model": pack.model,
    }

    if pack.queryset is not None:
        attrs["queryset"] = pack.queryset

    if view is PackViews.LIST:
        attrs["paginate_by"] = pack.paginate_by

    if view in (PackViews.CREATE, PackViews.UPDATE):
        attrs["form_class"] = pack.form_class
        attrs["fields"] = None if pack.form_class else pack.fields

        if pack.inlines:
            bases.append(InlineMixin)

    bases.append(generic_view)
    name = f"{pack.model.__name__}{view.name.title()}View"

    return type(name, tuple(bases), attrs)
