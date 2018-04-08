import re

from guake.globals import QUICK_OPEN_MATCHERS
from mock import Mock
from textwrap import dedent


def test_quick_open():
    chunk = dedent(
        """
        Traceback (most recent call last):
          File "./test.py", line 5, in <module>
              os.path('/bad/path')
          TypeError: 'module' object is not callable
        """
    )

    found = _execute_quick_open(chunk)
    assert found == [('./test.py', '5')]


def _execute_quick_open(chunk):
    found = []

    for line in chunk.split('\n'):
        for _1, _2, r in QUICK_OPEN_MATCHERS:
            g = re.compile(r).match(line)
            if g:
                found.append((g.group(1), g.group(2)))
    return found
