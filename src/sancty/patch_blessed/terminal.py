from blessed import sequences, terminal
from cwcwidth import wcswidth


class PatchedSequence(sequences.Sequence):
    def length(self):
        return wcswidth(self.padd(strip=True))


class Terminal(terminal.Terminal):
    def length(self, text: str) -> int:
        return PatchedSequence(text, self).length()
