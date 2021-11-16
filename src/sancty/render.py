from sancty.deps_types import Optional, Terminal, tm, wcswidth, Protocol, Callable


class ReplaceRender:
    new_render: list
    new_paragraphs: list

    def __init__(self, ren, par):
        self.new_render = ren
        self.new_paragraphs = par


default_replace_dict = {
    "clr": (-1, "Clears all text"),
    "help": (-2, "Shows all slash commands"),
}


def default_special_slash_fn(_control_num, render_copy, paragraphs_copy) -> tuple[list, list]:
    return render_copy, paragraphs_copy


class RendererProtocol(Protocol):
    was_resizing: bool
    empty_queue: bool
    exited: bool = False
    term: Terminal
    replace_dict: dict[str, tuple[int, str] | str]
    special_slash_fn: Callable[[int, list, list], tuple[list, list]]

    def print_terminal(self) -> None:
        """Blocking print loop."""

    def has_exited(self) -> bool:
        """Program has initiated exit."""

    def is_resizing(self) -> bool:
        """Terminal is resizing."""

    def update_values(self, values) -> tuple[bool, list]:
        """Update print buffer."""

    def render_current(self, render_array, paragraph_ends, val=None, rewrap=False,
                       replace: Optional[ReplaceRender] = None) -> tuple[list, list]:
        """Perform printing operation."""

    def slash_replace(self, text) -> int | str:
        """Get slash control string result."""

    def check_slash(self, slash_text, render_array, paragraph_ends) -> tuple[str, list, Optional[ReplaceRender]]:
        """Check if there is a slash match."""

    def backspace(self, current_text, slash_text, matching_slash, width_deleted=False) -> tuple[str, str, bool]:
        """Perform backspace operation on text."""

    def handle_backspace(self, render_array, slash_text, matching_slash,
                         changed_lines=False) -> tuple[list, bool, str, bool]:
        """Handle backspace for terminal text."""

    def do_exit(self) -> None:
        """Exit"""


class Renderer(RendererProtocol):

    def __init__(self, term, replace_dict=None, special_slash_fn=None):
        if replace_dict is None:
            self.replace_dict = default_replace_dict
        else:
            self.replace_dict = replace_dict
        if special_slash_fn is None:
            self.special_slash_fn = default_special_slash_fn
        else:
            self.special_slash_fn = special_slash_fn

        self.term = term

    def print_terminal(self):
        values = []
        i = 0
        render_array = ['']
        paragraph_ends = []
        was_resizing = False
        matching_slash: bool = False
        slash_text: str = '\\'

        while not self.has_exited():
            # with self.term.location(x=0, y=self.term.height - 1):
            #     print(f'i {i}', end='', flush=True)
            empty_queue, values = self.update_values(values)
            if self.is_resizing():
                was_resizing = True
                if empty_queue:
                    tm.sleep(0.003)
                continue
            if was_resizing:
                render_array, paragraph_ends = self.render_current(render_array, paragraph_ends, rewrap=True)
                was_resizing = False
            if len(render_array) == 0:
                render_array = ['']
            if len(values) > 0:
                val = values.pop(0)
                if val and not val.is_sequence:
                    match val:
                        case "\\":
                            if matching_slash:
                                slash_text = "\\"
                            matching_slash = True
                        case char if char.isspace():
                            if matching_slash:
                                matching_slash = False
                                slash_text = "\\"
                        case _:
                            if matching_slash:
                                slash_text += val

                    render_array, paragraph_ends = self.render_current(render_array, paragraph_ends, val=val)
                    # final_render_lines = render_current(term, render_array.pop(-1), val)
                    # render_array += final_render_lines
                    if matching_slash:
                        slash_text, new_render, replace_render = self.check_slash(slash_text, render_array,
                                                                                  paragraph_ends)
                        if replace_render is not None:
                            render_array, paragraph_ends = self.render_current(render_array, paragraph_ends,
                                                                               replace=replace_render)
                            matching_slash = False

                elif val.is_sequence:
                    if val.code in (self.term.KEY_BACKSPACE, self.term.KEY_DELETE):
                        render_array, changed_lines, slash_text, matching_slash = self.handle_backspace(render_array,
                                                                                                        slash_text,
                                                                                                        matching_slash)
                        if paragraph_ends and changed_lines and len(render_array) - 2 == paragraph_ends[-1]:
                            paragraph_ends.pop(-1)
                        render_array, paragraph_ends = self.render_current(render_array, paragraph_ends,
                                                                           rewrap=changed_lines)
                    # wrapped, current_text = render_current(term, wrapped, current_text)
                    elif val.code == self.term.KEY_ENTER:
                        if matching_slash:
                            matching_slash = False
                            slash_text = "\\"
                        fin_paragraph = paragraph_ends[-1] if paragraph_ends else -1
                        paragraph_ends.append(max(len(render_array) - 1, fin_paragraph + 1))
                        render_array, paragraph_ends = self.render_current(render_array, paragraph_ends, rewrap=True)

                if len(val) > 0:
                    pass
            else:
                tm.sleep(0.003)
            i += 1
            # with self.term.location(x=0, y=self.term.height - 1):
            #     print(f'slsh {slash_text}', end='', flush=True)

        self.do_exit()

    def has_exited(self) -> bool:
        return True

    def is_resizing(self) -> bool:
        return False

    def update_values(self, values) -> tuple[bool, list]:
        values = []
        return False, values

    def render_current(self, render_array, paragraph_ends, val=None, rewrap=False,
                       replace: Optional[ReplaceRender] = None) -> tuple[list, list]:
        # if render_array is not None:
        #     tm.sleep(1)
        new_paragraphs = paragraph_ends
        move_up = -1
        # if val is not None and current_text is not None:
        #     current_text += val
        if rewrap or replace is not None:
            # tm.sleep(1)
            final_k = len(render_array) - 1
            for k, line in enumerate(render_array):

                if k == final_k or len(line) == 0:
                    line += 'a'
                move_up += len(self.term.wrap(line, width=self.term.width, drop_whitespace=False))

            if replace is not None:
                render_array = replace.new_render
                paragraph_ends = replace.new_paragraphs
            wrapped = []
            new_paragraphs = []
            prev_pend = 0
            for i, pend in enumerate(paragraph_ends):
                paragraph = render_array[prev_pend:pend + 1]
                par_wrap = self.term.wrap(''.join(paragraph), drop_whitespace=False)
                wrapped += (par_wrap if len(par_wrap) > 0 else [''])
                new_paragraphs.append(len(wrapped) - 1)
                prev_pend = pend + 1
            if len(render_array) > prev_pend:
                final_paragraph = render_array[prev_pend:]
                par_wrap = self.term.wrap(''.join(final_paragraph), drop_whitespace=False)
                wrapped += (par_wrap if len(par_wrap) > 0 else [''])
            else:
                wrapped += ['']

            render_array = wrapped
            # with self.term.location(x=0, y=self.term.height - 1):
            #     print(f'mvup {move_up} + wr {len(wrapped)}', end='', flush=True)
            # tm.sleep(1)
        else:
            last_line = render_array.pop(-1)
            # if move_up_add == -1:
            #     with self.term.location(x=0, y=self.term.height - 1):
            #         print(f'ra {len(render_array)} + ll {len(last_line)}', end='', flush=True)
            #         tm.sleep(2)
            if val is not None:
                last_line += val

            wrapped: list[str] = self.term.wrap(last_line, drop_whitespace=False)
            if len(wrapped) == 0:
                wrapped = ['']
            # if move_up_add == -1: with self.term.location(x=0, y=self.term.height - 1): print(f'wr {len(wrapped)} +
            # wr0 {len(wrapped[0]) if len(wrapped) > 0 else "Z"}', end='', flush=True) tm.sleep(2)
            render_array += wrapped

        move_up = '' if move_up <= 0 else self.term.move_up(move_up)
        print(self.term.clear_bol + move_up + self.term.move_x(0), end='',
              flush=True)
        # if rewrap:
        #     tm.sleep(3)
        if render_array is not None:
            # with self.term.location(x=0, y=self.term.height - 1):
            #     print(len(render_array))
            # with self.term.location(x=0, y=self.term.height - 2):
            #     print(str(move_up) + ' ' + repr(move_up))
            # tm.sleep(4)
            pass
        print(self.term.clear_eos + "\n\r".join(wrapped), end='',
              flush=True)

        # with self.term.location(x=0, y=self.term.height - 2):
        #     print(f'a {len(render_array[-1])} r {len(render_array)} pe {len(new_paragraphs)}', end='', flush=True)
        # with self.term.location(x=0, y=term.height - 1):
        #     print(f'pea {paragraph_ends}', end='', flush=True)
        return render_array, new_paragraphs

    def slash_replace(self, text) -> str | tuple[int, str]:
        actual_text = text.lstrip('\\')
        if actual_text in self.replace_dict.keys():
            return self.replace_dict[actual_text]

    def check_slash(self, slash_text, render_array, paragraph_ends) -> tuple[str, list, Optional[ReplaceRender]]:
        slash_match = self.slash_replace(slash_text)
        do_render = slash_match is not None
        new_render = render_array
        if do_render:
            new_render = render_array.copy()
            new_paragraphs = paragraph_ends.copy()
            new_render[-1] = new_render[-1].rstrip(slash_text)
            if isinstance(slash_match, tuple) and slash_match:
                if slash_match[0] == -1:
                    new_render = ['']
                    new_paragraphs = []
                elif slash_match[0] == -2:
                    new_render = [f'{key} : {value[-1] if isinstance(value, tuple) else value}\n' for key, value in
                                  self.replace_dict.items()]
                    new_paragraphs = [i for i in range(len(new_render))]
                else:
                    new_render, new_paragraphs = self.special_slash_fn(slash_match[0], new_render, new_paragraphs)
            else:
                new_render[-1] += slash_match
            slash_text = "\\"
            replace_render = ReplaceRender(new_render, new_paragraphs)
        else:
            replace_render = None
        return slash_text, new_render, replace_render

    def backspace(self, current_text, slash_text, matching_slash, width_deleted=False) -> tuple[str, str, bool]:
        text_len = len(current_text)
        prev_prev = ''
        prev = ''
        do_backspace = True
        if text_len > 1:
            prev_prev = current_text[-2]
            prev = current_text[-1]
        elif text_len > 0:
            prev = current_text[-1]
        else:
            do_backspace = False
        if do_backspace:
            if prev:
                removed_char = current_text[-1]
                current_text = current_text[:-1]
                if removed_char == "\\":
                    matching_slash = False
                    slash_text = "\\"
                elif matching_slash:
                    slash_text = slash_text[:-1]
            if not width_deleted and wcswidth(prev) != 0:
                width_deleted = True
            if wcswidth(prev_prev) == 0 or (wcswidth(prev) == 0 and not width_deleted):
                current_text, slash_text, matching_slash = self.backspace(current_text, slash_text, matching_slash,
                                                                          width_deleted=width_deleted)

        return current_text, slash_text, matching_slash

    def handle_backspace(self, render_array, slash_text, matching_slash, changed_lines=False) -> tuple[
        list, bool, str, bool]:
        if len(render_array[-1]) > 0:
            render_array[-1], slash_text, matching_slash = self.backspace(render_array[-1], slash_text, matching_slash)
        elif len(render_array) > 1:
            changed_lines = True
        return render_array, changed_lines, slash_text, matching_slash

    def do_exit(self):
        pass
