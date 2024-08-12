from django.apps import apps


def register(model):
    """
    @register(Author)
    @register('app.Model')
    class AuthorPack(viewpack.ModelPack):
        pass
    """
    from viewpack import ModelPack, packs

    def _model_pack_wrapper(pack_cls):
        if not model:
            raise ValueError("A model must be passed to be register.")

        model_class = model

        if isinstance(model, str):
            try:
                app_name, model_name = model.split(".")
                model_class = apps.get_model(app_name, model_name)
            except ValueError:
                raise ValueError("Does not exist '%s' model" % model)

        if not issubclass(pack_cls, ModelPack):
            raise ValueError("Wrapped class must subclass ModelPack.")

        packs.register(model_class, pack_cls=pack_cls)

        return pack_cls

    return _model_pack_wrapper
