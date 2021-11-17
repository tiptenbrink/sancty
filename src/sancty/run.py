from sancty.deps_types import Queue, Event, QueueEmpty, Terminal, Callable
from sancty.read import Reader, ReaderProtocol
from sancty.render import Renderer, RendererProtocol
import multiprocessing as mp


def create_process_reader(clss: ReaderProtocol):
    class ProcessReadr(clss):
        render_queue: Queue
        exit_event: Event
        resizing_event: Event

        def __init__(self, term, render_queue, exit_event, resizing_event):
            super().__init__(term)
            self.exit_event = exit_event
            self.render_queue = render_queue
            self.resizing_event = resizing_event

        def has_exited(self):
            return self.exit_event.is_set()

        def resizing_set(self):
            self.resizing_event.set()
            self.resizing = True

        def resizing_clear(self):
            self.resizing_event.clear()
            self.resizing = False

        def send_values(self, values):
            self.render_queue.put(values)

        def queue_size(self) -> int:
            return self.render_queue.qsize()

        def exit_set(self):
            self.exit_event.set()
            self.exited = True

    return ProcessReadr


def create_process_renderer(clss: RendererProtocol):
    class ProcessRendr(clss):
        render_queue: Queue
        exit_event: Event
        resizing: Event

        def __init__(self, term, render_queue, exit_event, resizing, replace_dict=None, special_slash_fn=None,
                     replace_dict_add=True, overwrite=False):
            super().__init__(term, replace_dict, special_slash_fn, replace_dict_add, overwrite)
            self.render_queue = render_queue
            self.exit_event = exit_event
            self.resizing = resizing

        def has_exited(self) -> bool:
            return self.exit_event.is_set()

        def is_resizing(self) -> bool:
            return self.resizing.is_set()

        def update_values(self, values) -> tuple[bool, list]:
            try:
                new_values = self.render_queue.get(block=False)
                values += new_values
                return False, values
            except QueueEmpty:
                return True, values

        def do_exit(self):
            self.exit_event.set()

    return ProcessRendr


def reader_process_start(term, reader, render_queue, exit_event, resizing):
    if reader is not None:
        reader_cls = create_process_reader(reader)
    else:
        reader_cls = create_process_reader(Reader)

    # term = Terminal()
    print("\n" * 20 + term.move_x(0) + term.move_up(20))
    reader_inst: ReaderProtocol = reader_cls(term, render_queue, exit_event, resizing)
    reader_inst.read_terminal()


def render_process_start(term, renderer, render_queue, exit_event, resizing, replace_dict, special_slash_fn,
                         replace_dict_add, overwrite):
    if renderer is not None:
        renderer_cls = create_process_renderer(renderer)
    else:
        renderer_cls = create_process_renderer(Renderer)

    renderer_inst: RendererProtocol = renderer_cls(term, render_queue, exit_event, resizing, replace_dict,
                                                   special_slash_fn, replace_dict_add, overwrite)
    renderer_inst.print_terminal()


def start_terminal(renderer=None, reader=None, replace_dict: dict[str, str | tuple[int, str]] = None,
                   special_slash_fn: Callable[[int, list, list], tuple[list, list]] = None,
                   replace_dict_add: bool = True, overwrite: bool = False):

    render_queue = mp.Manager().Queue()
    exit_event = mp.Manager().Event()
    resizing = mp.Manager().Event()

    term = Terminal()

    print("Welcome to Sancty Text! (Test1)")
    print("Press 'ESC', 'CTRL+C' or 'CTRL+D' to quit. "
          "Type \\help for a list of '\\\\' commands (also clears all text).")
    # print("\n" * 20 + term.move_x(0) + term.move_up(20))

    input_process = mp.Process(target=reader_process_start, args=(term, reader, render_queue, exit_event, resizing,))
    render_process = mp.Process(target=render_process_start, args=(term, renderer, render_queue, exit_event, resizing,
                                                                   replace_dict, special_slash_fn, replace_dict_add,
                                                                   overwrite,))

    processes = []

    input_process.start()
    processes.append(input_process)
    render_process.start()
    processes.append(render_process)

    for process in processes:
        process.join()
