from enum import StrEnum, auto

class EnumArg(StrEnum):
    @classmethod
    def arg(cls):
        return dict(
            type=cls,
            choices=list(map(lambda e: e.value, cls))
        )


class TokenScoresFormat(EnumArg):
    FIRST_TOKEN = auto()
    RESPONSE_TOKENS = auto()
