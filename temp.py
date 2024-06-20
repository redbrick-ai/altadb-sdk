import time
import random
from typing import Any, Coroutine, List
import tqdm  # type: ignore
import asyncio

from altadb.utils.async_utils import gather_with_concurrency


async def sleep(index: int, upload_callback: tqdm.tqdm) -> int:
    n = max(1, random.randint(1, index + 1))
    await asyncio.sleep(n)
    if upload_callback:
        upload_callback(index, n)
    return n


async def main(index: int, progress_bar: tqdm.tqdm) -> int:
    coros = [
        sleep(i, upload_callback=lambda _, __: progress_bar.update(1))
        for i in range(index)
    ]
    res = await gather_with_concurrency(5, coros, "Sleeping", False)
    return sum(res)


async def wait(progress_bar):
    await asyncio.sleep(10)


async def collector(l: List[int], progress_bar: tqdm.tqdm) -> int:
    t = await gather_with_concurrency(
        5, [main(_, progress_bar) for _ in l], "Sleeping", False
    )
    return sum(t)


def hello() -> None:
    N = 5
    X = [random.randint(1, 10) for _ in range(N)]
    print(f"List of random numbers: {X}")
    progress_bar = tqdm.tqdm(desc="Uploading all files", total=sum(X))
    time.sleep(5)
    # print(f"Sum of random numbers: ")
    asyncio.run(collector(X, progress_bar))
    # asyncio.run(wait(progress_bar))


hello()
