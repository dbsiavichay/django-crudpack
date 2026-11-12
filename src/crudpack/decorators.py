def register(model, site=None):
    """
    Register a ``ModelPack`` subclass for ``model``::

        @register(Author)
        @register("app_label.ModelName")
        class AuthorPack(ModelPack):
            ...

    ``site`` is the ``PackService`` to register on; defaults to ``crudpack.packs``.
    """

    def _model_pack_wrapper(pack_cls):
        from crudpack.services.packs import packs

        (site or packs).register(model, pack_cls)

        return pack_cls

    return _model_pack_wrapper
