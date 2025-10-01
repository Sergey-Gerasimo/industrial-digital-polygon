from dataclasses import dataclass


@dataclass(frozen=True, eq=False)
class AplicationException(Exception):
    @property
    def message(self):
        return "Ошибка приложения"
