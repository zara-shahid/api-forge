"""
Shared retry helper for LangChain structured-output calls.

Day 8 hardening: Groq's structured output occasionally fails to parse
its own function call, especially on longer completions (seed data was
the worst offender, but schema and route generation aren't immune).
One retry catches the vast majority of these transient failures
without masking a real, repeated problem -- if every attempt fails,
that's a genuine issue worth surfacing, not silently swallowing.
"""

import time


def call_with_retry(fn, *args, attempts: int = 2, delay_seconds: float = 1.0, on_retry=None, **kwargs):
    """Call fn(*args, **kwargs), retrying up to `attempts` times total.

    Sleeps `delay_seconds` between attempts (Groq's transient failures
    are sometimes rate-limit related, so a small pause helps). Re-raises
    the last exception if every attempt fails -- callers decide how to
    turn that into a clean HTTP error.
    """
    last_error = None
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if on_retry:
                on_retry(attempt, exc)
            if attempt < attempts - 1:
                time.sleep(delay_seconds)
    raise last_error