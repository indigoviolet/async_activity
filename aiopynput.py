from __future__ import annotations
import asyncio

import attr
import janus
from pynput import keyboard, mouse
from datetime import datetime
from typing import Callable


@attr.s
class AioPynput:
    _queue: janus.Queue = attr.ib(init=False)
    _mouse_listener: mouse.Listener = attr.ib(init=False)
    _keyboard_listener: keyboard.Listener = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self._queue = janus.Queue(loop=asyncio.get_event_loop())
        self._mouse_listener = mouse.Listener(
            on_move=self._putter("move"),
            on_click=self._putter("click"),
            on_scroll=self._putter("scroll"),
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._putter("press"), on_release=self._putter("release")
        )

    def start(self) -> AioPynput:
        self._mouse_listener.start()
        self._keyboard_listener.start()

        self._mouse_listener.wait()
        self._keyboard_listener.wait()
        return self

    def stop(self) -> None:
        # this sometimes hangs. it's unclear if it is necessary to
        # stop these, since they are daemon threads and will die on
        # program exit.
        #
        # Don't think this is actually doing anything: (based on https://www.roguelynn.com/words/asyncio-sync-and-threaded/)
        # self._keyboard_listener._tstate_lock.release()
        # self._mouse_listener._tstate_lock.release()
        #
        # self._keyboard_listener.stop()
        # self._mouse_listener.stop()
        pass

    def _putter(self, evt: str) -> Callable[..., None]:
        return lambda *args: self.sync_q.put_nowait((datetime.now().timestamp(), evt, args))

    @property
    def sync_q(self):
        return self._queue.sync_q

    @property
    def async_q(self):
        return self._queue.async_q
