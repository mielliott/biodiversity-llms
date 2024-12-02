import asyncio
import threading
import queue
from async_stream import AsyncFileLikeObject
from aiohttp import ClientSession
import json
import aiohttp


class RunStatus:
    running = True

def wrap_async_iter(ait, loop):
    """Wrap an asynchronous iterator into a synchronous one"""
    q = queue.Queue()
    _END = object()

    async def aiter_to_queue():
        try:
            async for item in ait:
                q.put(item)
        finally:
            q.put(_END)

    def yield_queue_items():
        while True:
            next_item = q.get()
            if next_item is _END:
                break
            yield next_item
        # After observing _END we know the aiter_to_queue coroutine has
        # completed.  Invoke result() for side effect - if an exception
        # was raised by the async iterator, it will be propagated here.
        async_result.result()

    async_result = asyncio.run_coroutine_threadsafe(aiter_to_queue(), loop)
    return yield_queue_items()

async def create_req_object(queries, queue):
    for idx, query in enumerate(queries):
        request = {
            "custom_id": f"request-{idx}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "content": query[0]
            },
        }
        await queue.put((idx, query))
        yield (json.dumps(request) + '\n').encode()


async def upload_to_openai(file_like_obj, queue, run_status_obj):
    url = 'https://api.openai.com/v1/files'
    headers = {
        'Authorization': 'Bearer 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'
    }

    async with ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('purpose', 'batch')
        # aggregate data from file_like_obj here - asyncgenerator for logs
        data.add_field('file', file_like_obj, filename='batch.jsonl')
        async with session.post(url, headers=headers, data=data) as response:
            await queue.put(('response', str(response)))
            run_status_obj.running = False
            return await response.json()


async def flush_queue(queue, run_status_obj):
    while run_status_obj.running:
        item = await queue.get()
        yield {
            "request id": item[0],
            "query": item[1]
        }


async def create_batch(data, queue, run_status_obj):
    objects = create_req_object(data, queue)
    file = AsyncFileLikeObject(objects)
    file_data = file.read()
    response = await upload_to_openai(file_data, queue, run_status_obj)
    print(response['id'])
    return response


def data_file():
    return iter(['this is a random data string which is going to be written to a file', 'this is a second line of data', 'this is a third line of data', 'this is a fourth line of data', 'this is a fifth line of data', 'this is a sixth line of data', 'this is a seventh line of data', 'this is a eighth line of data', 'this is a ninth line of data', 'this is a tenth line of data', 'this is an eleventh line of data', 'this is a twelfth line of data', 'this is a thirteenth line of data', 'this is a fourteenth line of data', 'this is a fifteenth line of data', 'this is a sixteenth line of data', 'this is a seventeenth line of data', 'this is a eighteenth line of data', 'this is a nineteenth line of data', 'this is a twentieth line of data', 'this is a twenty-first line of data', 'this is a twenty-second line of data', 'this is a twenty-third line of data', 'this is a twenty-fourth line of data', 'this is a twenty-fifth line of data', 'this is a twenty-sixth line of data', 'this is a twenty-seventh line of data', 'this is a twenty-eighth line of data', 'this is a twenty-ninth line of data', 'this is a thirtieth line of data', 'this is a thirty-first line of data', 'this is a thirty-second line of data', 'this is a thirty-third line of data', 'this is a thirty-fourth line of data', 'this is a thirty-fifth line of data', 'this is a thirty-sixth line of data', 'this is a thirty-seventh line of data', 'this is a thirty-eighth line of data', 'this is a thirty-ninth line of data', 'this is a fortieth line of data', 'this is a forty-first line of data', 'this is a forty-second line of data', 'this is a forty-third line of data', 'this is a forty-fourth line of data', 'this is a forty-fifth line of data', 'this is a forty-sixth line of data', 'this is a forty-seventh line of data', 'this is a forty-eighth line of data', 'this is a forty-ninth line of data', 'this is a fiftieth line of data'])


# create an asyncio loop that runs in the background to
# serve our asyncio needs
loop = asyncio.get_event_loop()
thread = threading.Thread(target=loop.run_forever, daemon=True)
thread.start()

item_queue = asyncio.Queue(10)
data = data_file()
run_status_obj = RunStatus()
asyncio.run_coroutine_threadsafe(create_batch(data, item_queue, run_status_obj), loop)
for item in wrap_async_iter(flush_queue(item_queue, run_status_obj), loop):
    if item["request id"] == 'response':
        continue
    print(item)
