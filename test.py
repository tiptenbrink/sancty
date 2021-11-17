import sancty
from blessed import Terminal
from blessed.formatters import NullCallableString
import multiprocessing as mp
import pickle


def test_hi(term_test):
    print("hi")


if __name__ == '__main__':
    # mp.set_start_method('spawn')
    # term = Terminal()
    # process = mp.Process(target=test_hi, args=(term,))
    # process.start()
    #
    #
    # process.join()

    sancty.start_terminal()
