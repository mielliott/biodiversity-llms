from io import IOBase
from typing import IO, Iterator


class FileLikeObject(IOBase, IO[bytes]):
    def __init__(self, iterator: Iterator):
        self.chunk = b""
        self.offset = 0
        self.source = iterator

    def load(self, size):
        while size:
            if self.offset == len(self.chunk):
                try:
                    self.chunk = next(self.source)
                except StopIteration:
                    return
            to_yield = min(size, len(self.chunk) - self.offset)
            self.offset += to_yield
            size -= to_yield
            part = self.chunk[self.offset - to_yield:self.offset]
            yield part

    def read(self, size=-1):
        chunks = []
        for part in self.load(float("inf") if size is None or size < 0 else size):
            chunks.append(part)
        return b"".join(chunks)
