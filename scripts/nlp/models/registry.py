from typing import Dict, Type
from .model import Model


class ModelRegistry:
    _models: Dict[str, Type[Model]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(model_class: Type[Model]):
            cls._models[name] = model_class
            return model_class
        return decorator

    @classmethod
    def get_model(cls, name: str) -> Type[Model] | None:
        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return list(cls._models.keys())
