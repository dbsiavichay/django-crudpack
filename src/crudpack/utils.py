import inspect
from importlib import import_module


def import_class(module_name, class_name):
    cls = None
    try:
        module = import_module(module_name)
        members = inspect.getmembers(module, inspect.isclass)
        for name, klass in members:
            if name == class_name:
                cls = klass
                break
    except ModuleNotFoundError:
        print("Not found %s" % module_name)
    return cls


def import_mixin(name):
    mixin = import_class("superadmin.mixins", name)
    return mixin


def import_all_mixins():
    mixins = list()
    names = (
        "PermissionRequiredMixin",
        "BreadcrumbMixin",
        "UrlMixin",
        "TemplateMixin",
    )
    for name in names:
        mixin = import_mixin(name)
        if mixin:
            mixins.append(mixin)

    return mixins
