from sancty.deps_types import Terminal, tm, Protocol


class ReaderProtocol(Protocol):
    term: Terminal
    exited: bool = False
    resizing: bool = False

    def read_terminal(self) -> None:
        """Blocking input read loop."""

    def exit_set(self) -> None:
        """Signal program should exit."""

    def resizing_set(self) -> None:
        """Signal resizing has started."""

    def resizing_clear(self) -> None:
        """Signal resizing is done."""

    def send_values(self, values) -> None:
        """Send input to print buffer."""

    def queue_size(self) -> int:
        """Get size of sent print buffer."""


class Reader(ReaderProtocol):

    def __init__(self, term):
        self.term = term

    def read_terminal(self) -> None:
        with self.term.raw():
            current_time = 0
            values = []
            i = 0
            wait_time = 15000
            hw = (self.term.height, self.term.width)
            try:
                while not self.has_exited():
                    new_hw = (self.term.height, self.term.width)
                    if new_hw != hw:
                        self.resizing_set()
                        hw = new_hw
                        tm.sleep(0.05)
                    else:
                        self.resizing_clear()
                    if not self.resizing:
                        start_time = tm.process_time_ns()
                        val = self.term.inkey(timeout=0.005)

                        if val == chr(3) or val == chr(4) or val.code == self.term.KEY_ESCAPE:
                            break
                        if not val == '':
                            values.append(val)

                        current_time += tm.process_time_ns() - start_time

                        if i % 1000 == 0:
                            wait_time = 15000 + self.queue_size() * 1e4
                        if current_time > wait_time and len(values) > 0:
                            self.send_values(values)
                            values = []
                            current_time = 0
                        i += 1
                    else:
                        tm.sleep(0.003)
                    # if i % 1000 == 0:
                    #     with self.term.location(x=0, y=term.height - 3):
                    #         print(term.clear_eol + str(i) + ':' + str(len(values)) + f':qs{render_queue.qsize()}', end='',
                    #               flush=True)
                self.exit_set()
            except BaseException as bse:
                self.exit_set()
                print()
                raise bse

    def has_exited(self) -> bool:
        return self.exited

    def exit_set(self) -> None:
        self.exited = True

    def resizing_set(self) -> None:
        self.resizing = True

    def resizing_clear(self) -> None:
        self.resizing = False

    def send_values(self, values) -> None:
        pass

    def queue_size(self) -> int:
        return 0
