from enum import StrEnum, auto

class EnumArg(StrEnum):
    @classmethod
    def choices(cls):
        return list(map(lambda e: e.value, cls))


class TokenScoresFormat(EnumArg):
    FIRST_TOKEN = auto()
    RESPONSE_TOKENS = auto()
