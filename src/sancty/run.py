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

        def __init__(self, term, render_queue, exit_event, resizing, replace_dict=None, special_slash_fn=None):
            super().__init__(term, replace_dict, special_slash_fn)
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

    return ProcessRendr


ProcessReader = create_process_reader(Reader)

ProcessRenderer = create_process_renderer(Renderer)


def start_terminal(renderer=None, reader=None, replace_dict: dict[str, str | tuple[int, str]] = None,
                   special_slash_fn: Callable[[int, list, list], tuple[list, list]] = None):
    render_queue = mp.Manager().Queue()
    exit_queue = mp.Manager().Queue()
    exit_event = mp.Manager().Event()
    resizing = mp.Manager().Event()

    term = Terminal()

    if renderer is not None:
        renderer_cls = create_process_renderer(renderer)
    else:
        renderer_cls = ProcessRenderer
    if reader is not None:
        reader_cls = create_process_reader(reader)
    else:
        reader_cls = ProcessReader

    print("Welcome to Sancty Text!")
    print("Press 'ESC', 'CTRL+C' or 'CTRL+D' to quit. "
          "Type \\help for a list of '\\\\' commands (also clears all text).")
    print("\n" * 20 + term.move_x(0) + term.move_up(20))

    renderer: RendererProtocol = renderer_cls(term, render_queue, exit_event, resizing, replace_dict, special_slash_fn)
    reader: ReaderProtocol = reader_cls(term, render_queue, exit_event, resizing)

    input_process = mp.Process(target=reader.read_terminal)
    render_process = mp.Process(target=renderer.print_terminal)

    processes = []

    input_process.start()
    processes.append(input_process)
    render_process.start()
    processes.append(render_process)

    # render_window(render_queue, exit_event)

    for process in processes:
        process.join()


if __name__ == '__main__':
    start_terminal()
