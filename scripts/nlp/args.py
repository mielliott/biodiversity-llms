from enum import StrEnum, auto
from typing import Any

class EnumArg(StrEnum):
    @classmethod
    def arg(cls) -> dict[str, Any]:
        return dict(
            type=cls,
            choices=list(map(lambda e: e.value, cls))
        )


class TokenScoresFormat(EnumArg):
    FIRST_TOKEN = auto()
    RESPONSE_TOKENS = auto()
