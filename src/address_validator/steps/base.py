from abc import ABC, abstractmethod


class ValidationStep(ABC):
    @abstractmethod
    def __call__(self, ctx: dict) -> dict:
        pass
