from sancty import patch_blessed
import cwcwidth
import time
import queue
import threading
import typing

tm = time

Terminal = patch_blessed.Terminal
Queue = queue.Queue
Event = threading.Event
QueueEmpty = queue.Empty

wcswidth = cwcwidth.wcswidth

Optional = typing.Optional
Callable = typing.Callable
Protocol = typing.Protocol
Generic = typing.Generic
