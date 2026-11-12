# django-crudpack

[![PyPI](https://img.shields.io/pypi/v/django-crudpack)](https://pypi.org/project/django-crudpack/)
[![CI](https://github.com/dbsiavichay/django-crudpack/actions/workflows/ci.yml/badge.svg)](https://github.com/dbsiavichay/django-crudpack/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/django-crudpack)](https://pypi.org/project/django-crudpack/)

Build the list, create, update, detail and delete views of a Django model from a
single class, the same way you register a model in the admin.

```python
# library/packs.py
from crudpack import ModelPack, register

from .models import Book


@register(Book)
class BookPack(ModelPack):
    list_fields = ("title", "author", "status")
    paginate_by = 20
```

That gives you five URLs, each backed by Django's generic class-based views, with
a ready-to-render `pack_info` context. You write the templates.

## Requirements

- Python 3.10+
- Django 5.2 LTS, 6.0 or 6.1

## Installation

```bash
pip install django-crudpack
```

Add the app to your settings:

```python
INSTALLED_APPS = [
    # ...
    "crudpack",
]
```

Mount the registered packs in your URLconf, as you do with the admin:

```python
# urls.py
from django.urls import path

from crudpack import packs

urlpatterns = [
    path("crud/", packs.urls),
]
```

On startup crudpack imports the `packs.py` module of every installed app, so
registering there is enough.

## URLs

For a model `library.Book`, mounted under `crud/`:

| View   | URL                               | URL name                     |
| ------ | --------------------------------- | ---------------------------- |
| list   | `/crud/library/book/`             | `packs:library_book_list`    |
| create | `/crud/library/book/create/`      | `packs:library_book_create`  |
| update | `/crud/library/book/<pk>/update/` | `packs:library_book_update`  |
| detail | `/crud/library/book/<pk>/detail/` | `packs:library_book_detail`  |
| delete | `/crud/library/book/<pk>/delete/` | `packs:library_book_delete`  |

The `<pk>` converter follows the primary key type: `int`, `uuid` or `str`.

Use `{% url "packs:library_book_list" %}` in templates, or the ready-made
`pack_info.paths` described below.

## Registering

```python
from crudpack import ModelPack, packs, register


@register(Book)  # or @register("library.Book")
class BookPack(ModelPack): ...


packs.register(Author)  # defaults to a plain ModelPack
packs.register(Tag, TagPack)  # same as the decorator
```

To mount packs under another namespace, create your own registry and pass it to
the decorator:

```python
from crudpack import PackService, register

backoffice = PackService(name="backoffice")


@register(Book, site=backoffice)
class BookPack(ModelPack): ...


urlpatterns = [path("backoffice/", backoffice.urls)]  # backoffice:library_book_list
```

## Options

| Option                  | Default         | Description |
| ----------------------- | --------------- | ----------- |
| `allowed_views`         | all             | Tuple of `PackViews` members to expose (`LIST`, `CREATE`, `UPDATE`, `DETAIL`, `DELETE`). |
| `list_fields`           | `("__str__",)`  | Columns of the list view. |
| `detail_fields`         | all fields      | Fields of the detail view: a sequence of rows, or a dict of `{title: rows}`. |
| `default_labels`        | `{}`            | Custom labels keyed by field name. |
| `form_class`            | `None`          | Form for create and update. |
| `fields`                | `"__all__"`     | Fields of the generated form when there is no `form_class`. |
| `inlines`               | `{}`            | Formset classes keyed by name. See [Inlines](#inlines). |
| `queryset`              | default manager | Queryset used by every view. |
| `paginate_by`           | `None`          | Page size of the list view. |
| `max_paginate_by`       | `100`           | Upper bound for the `?paginate_by=` query parameter. |
| `default_success_url`   | list view       | Where create, update and delete redirect to. Placeholders such as `{id}` are filled with the object, as in Django. |
| `list_template_name`    | Django default  | Template of the list view (`<app>/<model>_list.html`). |
| `form_template_name`    | Django default  | Template of create and update (`<app>/<model>_form.html`). |
| `detail_template_name`  | Django default  | Template of the detail view (`<app>/<model>_detail.html`). |
| `delete_template_name`  | Django default  | Template of the delete view (`<app>/<model>_confirm_delete.html`). |
| `list_mixins`, `create_mixins`, `update_mixins`, `detail_mixins`, `delete_mixins` | `()` | Extra mixins for each view. |
| `url_list_suffix`, ...  | view name       | Suffix of each URL name. |

Options are validated when the pack is created: a misspelled field name or an
invalid option raises `ImproperlyConfigured` at startup, not on the first request.

When the list view is not allowed, create and update redirect to the detail view.
The delete view then needs `default_success_url`.

### Field names

`list_fields` and `detail_fields` accept:

- model fields: `"title"`. Fields with choices show their display value.
- methods and properties of the model: `"get_full_name"`, `"is_overdue"`.
- `"__str__"`: the object itself.
- paths through relations and JSON keys: `"author__name"`, `"metadata__color"`.

Rows group fields side by side. Each field gets a Bootstrap column width (`cols`)
that splits the 12-column grid between the fields of its row:

```python
detail_fields = {
    "General": ("title", ("author", "status")),  # title: 12, author/status: 6
    "Details": ("pages", "metadata__color"),
}
```

## Templates and context

crudpack does not ship templates. Every view gets the context of its Django
generic view (`object_list`, `object`, `form`, `page_obj`, ...) plus `pack_info`:

| Key             | Views                | Content |
| --------------- | -------------------- | ------- |
| `title`         | all                  | `verbose_name_plural` of the model. |
| `app_name`      | all                  | App label. |
| `model_name`    | all                  | Model name. |
| `paths`         | all                  | `{view: url}` for the allowed views. Update, detail and delete URLs only when there is an object. |
| `headers`       | list                 | `{field: label}`. |
| `rows`          | list                 | List of `(instance, {"data": {field: value}, "paths": {view: url}})`. |
| `start_index`, `end_index`, `count` | list | Position of the page in the results. |
| `fields`        | detail               | `{field: value}`. |
| `bs_fieldsets`  | detail               | `[{"title": ..., "fieldset": [{field: value + cols}, ...]}]`, one dict per row. |
| `inlines`       | create, update       | `{name: Inline}` when the pack has inlines. |

Each field value is a dict `{"value": ..., "label": ..., "type": ...}`, where
`type` is the lowercase Django field type (`charfield`, `foreignkey`,
`filefield`, ...) or the Python type for methods and JSON values. File fields
come as `{"name": ..., "url": ...}`.

Values are not marked as safe, so Django escapes them in templates. To render
HTML from a method, return it with `format_html()` or `mark_safe()`.

A minimal list template:

```django
<h1>{{ pack_info.title|capfirst }}</h1>
<a href="{{ pack_info.paths.create }}">New</a>
<table>
  <tr>{% for label in pack_info.headers.values %}<th>{{ label }}</th>{% endfor %}</tr>
  {% for instance, row in pack_info.rows %}
    <tr>
      {% for field in row.data.values %}<td>{{ field.value|default_if_none:"" }}</td>{% endfor %}
      <td><a href="{{ row.paths.detail }}">View</a> <a href="{{ row.paths.update }}">Edit</a></td>
    </tr>
  {% endfor %}
</table>
<p>{{ pack_info.start_index }}–{{ pack_info.end_index }} of {{ pack_info.count }}</p>
```

The list view accepts `?page=` and `?paginate_by=`. Invalid values of
`paginate_by` fall back to the pack's `paginate_by`.

## Forms with fieldsets

`crudpack.forms.ModelForm` accepts `Meta.fieldsets` with the same shape as
`detail_fields`. Fields named there are added to `Meta.fields`, and the form
exposes `bs_fieldsets`:

```python
from crudpack.forms import ModelForm


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ["title"]
        fieldsets = {
            "General": ("title", ("author", "status")),
            "Details": ("pages",),
        }
```

```django
{% for fieldset in form.bs_fieldsets %}
  <fieldset>
    <legend>{{ fieldset.title }}</legend>
    {% for row in fieldset.fieldset %}
      <div class="row">
        {% for field, cols in row %}<div class="col-{{ cols }}">{{ field.as_field_group }}</div>{% endfor %}
      </div>
    {% endfor %}
  </fieldset>
{% endfor %}
```

## Inlines

Edit related objects in the create and update views with formsets:

```python
from django.forms import inlineformset_factory

BookFormSet = inlineformset_factory(Author, Book, fields=("title", "pages"))


@register(Author)
class AuthorPack(ModelPack):
    inlines = {"books": BookFormSet}

    def post_save_inlines(self, instance):
        """Optional hook, called after the object and its inlines are saved."""
```

Each inline uses its name as the formset prefix. The object, its inlines and
`post_save_inlines()` are saved in one transaction, and only when the form and
every formset are valid.

In the template, `pack_info.inlines` maps each name to an object with `formset`,
`headers` (field labels), `errors` and `non_form_errors`:

```django
{% for name, inline in pack_info.inlines.items %}
  {{ inline.formset.management_form }}
  {{ inline.non_form_errors }}
  {% for form in inline.formset %}{{ form.as_div }}{% endfor %}
{% endfor %}
```

## Customizing views

Every view is a Django generic view. Its class is built once, when the URLs are
loaded, with this MRO:

```
<your mixins> → PackContextMixin → crudpack view mixin → Django generic view
```

Your mixins come first, so they can override any method and see the complete
`pack_info` in `get_context_data()`.

### Protecting views

crudpack does not check permissions: by default every view is public. Use
Django's auth mixins:

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class CanChangeBook(PermissionRequiredMixin):
    permission_required = "library.change_book"


@register(Book)
class BookPack(ModelPack):
    list_mixins = (LoginRequiredMixin,)
    detail_mixins = (LoginRequiredMixin,)
    create_mixins = (LoginRequiredMixin, CanChangeBook)
    update_mixins = (LoginRequiredMixin, CanChangeBook)
    delete_mixins = (LoginRequiredMixin, CanChangeBook)
```

## Development

```bash
make install   # uv sync
make test      # pytest with coverage
make lint      # ruff check and ruff format --check
make format    # apply ruff fixes and formatting
make build     # build and check the sdist and wheel
```

Run the tests against another Django or Python version:

```bash
uv run --isolated -p 3.14 --with "django~=6.0.0" pytest
```

## Releases

Releases are automatic. Every push to `master` runs the CI and then
[python-semantic-release](https://python-semantic-release.readthedocs.io/), which
reads the commit messages since the last tag and, if needed, bumps the version,
updates `CHANGELOG.md`, tags the commit, creates a GitHub release and publishes
the package to PyPI.

Commit messages (or PR titles, when squash merging) must follow
[Conventional Commits](https://www.conventionalcommits.org/):

| Commit                                    | Release                   |
| ----------------------------------------- | ------------------------- |
| `fix: ...`, `perf: ...`                   | patch (0.1.0 → 0.1.1)     |
| `feat: ...`                               | minor (0.1.0 → 0.2.0)     |
| `feat!: ...` or a `BREAKING CHANGE:` footer | minor while in 0.x, then major |
| `docs:`, `test:`, `ci:`, `chore:`, `refactor:`, `build:`, `style:` | no release |

## License

[MIT](LICENSE)
