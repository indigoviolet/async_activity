import asyncio
from datetime import datetime
from typing import List, NoReturn, Optional, Tuple

import attr
from async_timeout import timeout
from colorama import Fore

@attr.s
class ActivityMonitor:
    events_queue = attr.ib(kw_only=True)
    inactivity_window: float = attr.ib(kw_only=True)
    latest_event_time = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.latest_event_time = self._timenow()

    async def get(self) -> Tuple:
        new_latest_event_time = await self._get_latest_event_time()
        if new_latest_event_time is not None:
            self.latest_event_time = new_latest_event_time

        timenow = self._timenow()
        elapsed_since_latest_event = timenow - self.latest_event_time
        if elapsed_since_latest_event >= self.inactivity_window:
            result = (timenow, "inactivity", self.latest_event_time, elapsed_since_latest_event)
        else:
            result = (timenow, "activity", self.latest_event_time, elapsed_since_latest_event)
        return result

    async def _get_latest_event_time(self) -> Optional[float]:
        """
        Drain the queue and return the most recent event's timestamp, or None
        if the queue is empty for self.inactivity_window
        """
        try:
            while True:
                async with timeout(self.inactivity_window):
                    latest_ts, *_ = await self.events_queue.get()
                    if self.events_queue.empty():
                        return latest_ts
        except asyncio.TimeoutError:
            return None

    @staticmethod
    def _timenow() -> float:
        return datetime.now().timestamp()

@attr.s
class ActivityQueue:
    queue: asyncio.Queue = attr.ib(factory=asyncio.Queue, init=False)
    events_queue = attr.ib(kw_only=True)
    inactivity_window: float = attr.ib(kw_only=True)
    min_sleep_time: int = attr.ib(kw_only=True, default=30)

    def __attrs_post_init__(self):
        self.am = ActivityMonitor(events_queue, inactivity_window)

    async def run(self) -> NoReturn:
        while True:
            latest_event = await self.am.get()
            self.queue.put(latest_event)
            await asyncio.sleep(max(self.inactivity_window - latest_event[-1], self.min_sleep_time))



def async_q_tee(inq: asyncio.Queue, n=2) -> List[asyncio.Queue]:
    """
    Clones inq to n queues so that the items can be consumed multiple times independently

    this is probably nicer as a class so we don't have to do
    create_task() and instead can await on something

    """

    outqs: List[asyncio.Queue] = [asyncio.Queue() for i in range(n)]

    async def _tee() -> NoReturn:
        while True:
            item = await inq.get()
            await asyncio.gather(*(q.put(item) for q in outqs))

    asyncio.get_event_loop().create_task(_tee())
    return outqs


async def log_inactivity(q) -> NoReturn:
    while True:
        evt = await q.get()
        if evt[1] == "inactivity":
            print(Fore.MAGENTA + f"{evt=}")


async def log_activity(q) -> NoReturn:
    while True:
        evt = await q.get()
        if evt[1] == "activity":
            print(Fore.CYAN + f"{evt=}")
