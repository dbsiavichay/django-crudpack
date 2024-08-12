from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.urls import path

from .enums import PackViews
from .views import CreateView, DeleteView, DetailView, ListView, UpdateView

ALL_FIELDS = "__all__"

ALL_VIEWS = {
    PackViews.LIST: ListView,
    PackViews.CREATE: CreateView,
    PackViews.UPDATE: UpdateView,
    PackViews.DETAIL: DetailView,
    PackViews.DELETE: DeleteView,
}


class ModelPack:
    # Views
    model = None
    # Used on Create and Update views
    form_class = None
    # User for passed to Create and Update views for generate forms
    fields = None
    # Used for create ListView with de specified fields
    list_fields = ("__str__",)
    # Used for create DetailView with specified fields
    detail_fields = ()
    # Labels for fields
    default_labels = {}

    allowed_views = tuple(PackViews.__members__.values())
    default_success_url = None

    # Context
    # list_extra_context = {}
    form_extra_context = {}
    detail_extra_context = {}

    # Inlines
    inlines = {}

    # Templates
    list_template_name = None  # Says which list template use
    form_template_name = None  # Says which form template use
    detail_template_name = None  # Says which detail template use
    delete_template_name = None  # Says which delete template use
    _template_names = None

    # Mixins
    list_mixins = ()  # List of mixins that include in ListViews
    form_mixins = ()  # List of mixins that include in Create Views
    update_mixins = ()  # # List of mixins that include in Update Views
    detail_mixins = ()  # List of mixins that include in DetailViews
    delete_mixins = ()  # List of mixins that include in DetailViews

    # Prepopulate
    # slug_field = "slug"
    # prepopulate_slug = ()

    # Options for build queryset
    queryset = None  # Specified custom queryset
    paginate_by = None  # Specified if ListView paginated by

    # Filter and ordering
    # search_fields = ()  # Used for create searchs method by specified fields
    # filter_fields = ()
    # order_by = ()  # User for crate ordering methods by specified fields

    # Urls
    url_list_suffix = "list"
    url_create_suffix = "create"
    url_update_suffix = "update"
    url_detail_suffix = "detail"
    url_delete_suffix = "delete"

    def __init__(self, model, **kwargs):
        if not model:
            error = "The 'model' attribute must be specified."
            raise ImproperlyConfigured(error)

        try:
            self.list_fields = tuple(self.list_fields)
        except TypeError:
            raise ImproperlyConfigured(
                "The 'list_fields' must be an instance of tuple or list"
            )

        if not isinstance(self.detail_fields, (list, dict)):
            try:
                self.detail_fields = tuple(self.detail_fields)
            except TypeError:
                raise ImproperlyConfigured(
                    "The 'detail_fields' must be an instance of tuple, list or dict"
                )

        if not isinstance(self.default_labels, dict):
            raise ImproperlyConfigured(
                "The 'default_labels' must be an instance of dict"
            )

        if not isinstance(self.inlines, dict):
            raise ImproperlyConfigured("The 'inlines' must be an instance of dict")

        self.model = model

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not self.detail_fields:
            self.detail_fields = tuple(field.name for field in self.model._meta.fields)

        self._template_names = {
            PackViews.LIST: self.list_template_name,
            PackViews.CREATE: self.form_template_name,
            PackViews.UPDATE: self.form_template_name,
            PackViews.DETAIL: self.detail_template_name,
            PackViews.DELETE: self.delete_template_name,
        }

        if not isinstance(self.queryset, QuerySet):
            self.queryset = self.model._default_manager.all()

        if not self.allowed_views:
            error = "The 'allowed_views' attribute is required."
            raise ImproperlyConfigured(error)

        if not isinstance(self.allowed_views, (list, tuple)):
            error = "The 'allowed_views' attribute must be a list or tuple."
            raise ImproperlyConfigured(error)

        if not all([isinstance(enum, PackViews) for enum in self.allowed_views]):
            error = "The 'allowed_views' items must be a PackViews element."
            raise ImproperlyConfigured(error)

        if not self.form_class and not self.fields:
            self.fields = ALL_FIELDS

    @property
    def model_info(self):
        return self.model._meta.app_label, self.model._meta.model_name

    def post_save_inlines(self, instance):
        pass

    def get_base_url_name(self, suffix):
        url_suffix = getattr(self, "url_%s_suffix" % suffix)
        base_url_name = "%s_%s_%s" % (*self.model_info, url_suffix)
        return base_url_name

    def get_url_name(self, suffix):
        url_name = "pack:%s" % self.get_base_url_name(suffix)
        return url_name

    def get_urls(self):
        urlpatterns = []

        for enum in self.allowed_views:
            url_name = self.get_base_url_name(enum.value)
            route = "{0}/{1}/".format(enum.param, enum.suffix)
            route = route.replace("//", "/")
            route = route.lstrip("/") if route.startswith("/") else route
            View = ALL_VIEWS.get(enum)
            urlpatterns += [
                path(route=route, view=View.as_view(pack=self), name=url_name)
            ]

        return urlpatterns

    def get_paths(self, instance=None):
        paths = {}

        for enum in self.allowed_views:
            path = "/{0}/{1}/{2}/{3}/".format(
                *self.model_info,
                enum.kwarg,
                enum.suffix,
            )
            path = path.replace("//", "/").replace("//", "/")

            if instance:
                path = path.format(**instance.__dict__)

            paths.update({enum.name.lower(): path})

        return paths

    def get_default_success_url(self):
        if self.default_success_url:
            return self.default_success_url

        name_url = PackViews.LIST.name.lower()
        paths = self.paths
        success_url = paths.get(name_url)

        if not success_url:
            success_url = tuple(paths.values())[0]

        return success_url

    @property
    def urls(self):
        return self.get_urls()

    @property
    def paths(self):
        return self.get_paths()
