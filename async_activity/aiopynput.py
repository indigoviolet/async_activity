from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable

import attr
import janus
from pynput import keyboard, mouse  # type: ignore


@attr.s
class AioPynput:

    """
    stop(): We used to have it, but it sometimes hangs. it's unclear if it
    is necessary to stop the listener threads since they are daemon
    threads and will die on program exit.

    Don't think this is actually doing anything: (based on
    https://www.roguelynn.com/words/asyncio-sync-and-threaded/)

    self._keyboard_listener._tstate_lock.release()
    self._mouse_listener._tstate_lock.release()

    self._keyboard_listener.stop()
    self._mouse_listener.stop()
    """

    _queue: janus.Queue = attr.ib(init=False)
    _mouse_listener: mouse.Listener = attr.ib(init=False)
    _keyboard_listener: keyboard.Listener = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self._queue = janus.Queue()
        self._mouse_listener = mouse.Listener(
            on_move=self._make_putter("move"),
            on_click=self._make_putter("click"),
            on_scroll=self._make_putter("scroll"),
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._make_putter("press"), on_release=self._make_putter("release")
        )

    def start(self) -> AioPynput:
        self._mouse_listener.start()
        self._keyboard_listener.start()

        self._mouse_listener.wait()
        self._keyboard_listener.wait()
        return self

    def _make_putter(self, evt: str) -> Callable[..., None]:
        return lambda *args: self.sync_q.put_nowait(
            (datetime.now().timestamp(), evt, args)
        )

    @property
    def sync_q(self):
        return self._queue.sync_q

    @property
    def async_q(self):
        return self._queue.async_q
