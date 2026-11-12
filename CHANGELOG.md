# CHANGELOG

<!-- version list -->

## v0.1.0 (2026-11-12)

### Bug Fixes

- Rework views, URL resolution and field rendering
  ([`d139028`](https://github.com/dbsiavichay/django-crudpack/commit/d139028b91c7803c7b40b08fc9938ab85ae9fb41))

### Build System

- Migrate packaging to hatchling, uv and ruff
  ([`9647179`](https://github.com/dbsiavichay/django-crudpack/commit/9647179fe5968f74b7de9cd3bab846e0224ea25d))

### Continuous Integration

- Pin setup-uv to v10.3.3
  ([`5cb41df`](https://github.com/dbsiavichay/django-crudpack/commit/5cb41df31886e6cbf7c4e992d75c07bcd09212bc))

- Test pull requests and release to PyPI from master
  ([`1c36abc`](https://github.com/dbsiavichay/django-crudpack/commit/1c36abc260d0e4c0b54f4ef7187813a12887d0d3))

### Documentation

- Write README with setup, options, context and release process
  ([`623066e`](https://github.com/dbsiavichay/django-crudpack/commit/623066edae72d9785f32acf57466de02adf90777))

### Breaking Changes

- Form_mixins is replaced by create_mixins and update_mixins. pack_info.paths only has
  update/detail/delete URLs when there is an object. The views package exposes mixins and
  build_view() instead of wrapper view classes. Inline formsets use their name as the prefix.
  get_botstrap_fields() is renamed to get_bootstrap_fields() and FieldService._get_field_label() to
  get_field_label(). The unused form_extra_context and detail_extra_context options are removed.
  PackService.get_default_urls() is renamed to get_urls().


## v0.0.1 (2024-08-12)

- Initial Release
