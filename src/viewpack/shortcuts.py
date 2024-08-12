from django.conf import settings
from django.urls import NoReverseMatch, reverse


def get_slug_or_pk(object, slug_field=None):
    res = dict()
    field = slug_field if hasattr(object, slug_field) else "pk"
    if object:
        param = "slug" if hasattr(object, slug_field) else "pk"
        res.update({param: getattr(object, field)})
    return res


def get_urls_of_site(site, object=None, user=None):
    urls = {}
    app = site.model._meta.app_label
    model = site.model._meta.model_name
    kwargs = get_slug_or_pk(object, slug_field=site.slug_field)
    for action, perm in (("list", "view"), ("create", "add")):
        try:
            url_name = site.get_url_name(action)
            if not user:
                urls.update({action: reverse(url_name)})
            elif user.has_perm(f"{app}.{perm}_{model}"):
                urls.update({action: reverse(url_name)})
        except NoReverseMatch:
            if settings.DEBUG:
                print("DEBUG: Url not found: %s" % url_name)
    if not kwargs:
        return urls
    for action, perm in (
        ("update", "change"),
        ("detail", "view"),
        ("delete", "delete"),
    ):
        try:
            url_name = site.get_url_name(action)
            if not user:
                urls.update({action: reverse(url_name, kwargs=kwargs)})
            elif user.has_perm(f"{app}.{perm}_{model}"):
                urls.update({action: reverse(url_name, kwargs=kwargs)})
        except NoReverseMatch:
            if settings.DEBUG:
                print("DEBUG: Url not found: %s" % url_name)
    return urls
