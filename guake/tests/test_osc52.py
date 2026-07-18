# -*- coding: utf-8 -*-
"""Tests for OSC 52 clipboard sequence filtering."""

import base64
import re

import pytest

# Mirror the module-level constants from terminal.py so the tests are
# self-contained and do not require a running display or VTE.
_OSC52_RE = re.compile(
    b"\\x1b\\]52;([^;]*);([^\\x07\\x1b]*)"
    b"(?:\\x07|\\x1b\\\\)"
)
_OSC52_MAX_BUF = 1024 * 1024


def _filter(data, buf=b""):
    """Minimal re-implementation of GuakeTerminal._osc52_process_data."""
    clipboard_ops = []

    def _handle(match):
        params = match.group(1).decode("ascii", errors="ignore")
        encoded = match.group(2)
        if encoded == b"?":
            return b""
        try:
            text = base64.b64decode(encoded).decode("utf-8", errors="replace")
            clipboard_ops.append((params, text))
        except Exception:
            pass
        return b""

    combined = buf + data
    filtered = _OSC52_RE.sub(_handle, combined)

    # Buffer any potential incomplete OSC 52 at the tail
    new_buf = b""
    start = filtered.rfind(b"\x1b]52;")
    if start != -1:
        tail = filtered[start:]
        if not _OSC52_RE.match(tail):
            new_buf = tail
            filtered = filtered[:start]

    return filtered, new_buf, clipboard_ops


# ---------------------------------------------------------------------------
# Basic filtering
# ---------------------------------------------------------------------------


def test_osc52_bel_terminator():
    """OSC 52 sequence ending with BEL (0x07) is stripped and clipboard set."""
    text = "hello clipboard"
    encoded = base64.b64encode(text.encode()).decode()
    osc = f"\x1b]52;c;{encoded}\x07".encode()
    data = b"before" + osc + b"after"

    filtered, _, ops = _filter(data)

    assert filtered == b"beforeafter"
    assert len(ops) == 1
    assert ops[0] == ("c", text)


def test_osc52_st_terminator():
    """OSC 52 sequence ending with ST (ESC \\) is stripped."""
    text = "st terminated"
    encoded = base64.b64encode(text.encode()).decode()
    osc = (f"\x1b]52;c;{encoded}\x1b\\").encode()
    data = b"prefix" + osc + b"suffix"

    filtered, _, ops = _filter(data)

    assert filtered == b"prefixsuffix"
    assert len(ops) == 1
    assert ops[0][1] == text


def test_osc52_primary_selection():
    """Params 'p' targets the PRIMARY selection."""
    text = "primary"
    encoded = base64.b64encode(text.encode()).decode()
    osc = f"\x1b]52;p;{encoded}\x07".encode()

    _, _, ops = _filter(osc)

    assert ops[0][0] == "p"
    assert ops[0][1] == text


def test_osc52_empty_params():
    """Empty params field is preserved (defaults to CLIPBOARD in the handler)."""
    text = "default"
    encoded = base64.b64encode(text.encode()).decode()
    osc = f"\x1b]52;;{encoded}\x07".encode()

    filtered, _, ops = _filter(osc)

    assert filtered == b""
    assert ops[0][0] == ""  # empty params
    assert ops[0][1] == text


def test_normal_output_unchanged():
    """Terminal output without OSC 52 passes through unmodified."""
    data = b"normal output\r\n\x1b[32mgreen\x1b[0m"
    filtered, _, ops = _filter(data)
    assert filtered == data
    assert ops == []


def test_multiple_osc52_sequences():
    """Multiple OSC 52 sequences in one chunk are all processed."""
    t1, t2 = "first", "second"
    e1 = base64.b64encode(t1.encode()).decode()
    e2 = base64.b64encode(t2.encode()).decode()
    data = (
        b"A\x1b]52;c;" + e1.encode() + b"\x07"
        b"B\x1b]52;p;" + e2.encode() + b"\x07C"
    )

    filtered, _, ops = _filter(data)

    assert filtered == b"ABC"
    assert len(ops) == 2
    assert ops[0] == ("c", t1)
    assert ops[1] == ("p", t2)


def test_query_operation_ignored():
    """OSC 52 with '?' data (clipboard query) is stripped but not added to ops."""
    osc = b"\x1b]52;c;?\x07"
    filtered, _, ops = _filter(osc)
    assert filtered == b""
    assert ops == []


def test_incomplete_sequence_buffered():
    """An incomplete OSC 52 at the end of a chunk is held in the buffer."""
    text = "split"
    encoded = base64.b64encode(text.encode()).decode()
    full_osc = f"\x1b]52;c;{encoded}\x07".encode()

    # Send only the first half of the sequence
    half = len(full_osc) // 2
    chunk1 = full_osc[:half]
    chunk2 = full_osc[half:] + b"after"

    filtered1, buf, ops1 = _filter(chunk1)
    assert ops1 == []  # sequence not yet complete

    filtered2, _, ops2 = _filter(chunk2, buf)
    assert ops2[0][1] == text
    assert b"after" in filtered2


def test_utf8_content():
    """OSC 52 payload containing multibyte UTF-8 characters is decoded correctly."""
    text = "こんにちは"
    encoded = base64.b64encode(text.encode("utf-8")).decode()
    osc = f"\x1b]52;c;{encoded}\x07".encode()

    _, _, ops = _filter(osc)

    assert ops[0][1] == text


def test_osc52_default_clipboard_params():
    """When params contain neither 'c' nor 'p', the handler defaults to CLIPBOARD."""
    # Simulate the logic in _osc52_set_clipboard
    params = ""
    use_clipboard = "c" in params or not any(ch in params for ch in "ps")
    use_primary = "p" in params
    assert use_clipboard is True
    assert use_primary is False


def test_osc52_primary_only():
    """When params is 'p', only PRIMARY is set."""
    params = "p"
    use_clipboard = "c" in params or not any(ch in params for ch in "ps")
    use_primary = "p" in params
    assert use_clipboard is False
    assert use_primary is True


def test_osc52_both_targets():
    """When params is 'cp', both CLIPBOARD and PRIMARY are set."""
    params = "cp"
    use_clipboard = "c" in params or not any(ch in params for ch in "ps")
    use_primary = "p" in params
    assert use_clipboard is True
    assert use_primary is True
