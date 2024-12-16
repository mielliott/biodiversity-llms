from dataclasses import dataclass, MISSING
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


class BatchProcess(EnumArg):
    NONE = auto()
    WRITE = auto()
    READ = auto()


@dataclass(init=True, frozen=True)
class Params():
    model_name: str
    num_responses: int = 1
    max_tokens: int = 128
    combine_responses: bool = False
    batch_size: int = 10
    top_p: float = 1.0
    top_k: int = 0
    temperature: float = 1.0
    precision: str = "bfloat16"
    timeout: int = 10
    scores: TokenScoresFormat = TokenScoresFormat.RESPONSE_TOKENS
    batch: BatchProcess = BatchProcess.NONE

    def __getattr__(self, name: str) -> Any:
        cli_name = f"--{name}".replace("_", "-")
        raise RuntimeError(f"Require argument {cli_name} not set")


def get_default_params():
    fields = map(Params.__dataclass_fields__.get, Params.__dataclass_fields__)
    return {f.name: f.default for f in fields if f is not None and f.default is not MISSING}
