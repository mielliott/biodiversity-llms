from io import IOBase


class AsyncFileLikeObject(IOBase):
    def __init__(self, iterable):
        self.chunk = b""
        self.offset = 0
        self.i = iterable

    async def load(self, size):

        while size:
            if self.offset == len(self.chunk):
                try:
                    self.chunk = await anext(self.i)
                except StopAsyncIteration:
                    break
                else:
                    self.offset = 0
            to_yield = min(size, len(self.chunk) - self.offset)
            self.offset += to_yield
            size -= to_yield
            part = self.chunk[self.offset - to_yield:self.offset]
            yield part

    async def read(self, size=-1):
        chunks = []
        async for part in self.load(float("inf") if size is None or size < 0 else size):
            chunks.append(part)
        yield b"".join(chunks)
