"""Jev (System One) client via OpenCode Zen.

Calls ``https://opencode.ai/zen/v1/systemone`` directly over HTTP (instead of
the TypeSafe SDK) using the free ``jev-1.13-free`` model.  Jev does not
generate text: it evaluates a ``state`` against typed ``questions`` and
returns values with probabilities that code can use directly.
"""

from typing import Any

import requests

from config import JEV_MODEL, JEV_SYSTEM_ONE_URL, OPENCODE_API_KEY


class JevError(RuntimeError):
    """Raised when the system-one call fails (auth, network, HTTP error...)."""


def evaluate(state: Any, questions: dict[str, dict]) -> dict:
    """Evaluate *state* against typed *questions* with Jev via OpenCode Zen.

    Parameters
    ----------
    state:
        Plain text, a JSON object, or an array to evaluate.
    questions:
        Mapping of question name → question dict.  Question types:

        - ``noul``:    ``{"type": "noul", "instructions": "..."}``
        - ``choice``:  ``{"type": "choice", "instructions": "...",
                          "criteria": {"a": "...", "b": "..."}}``
        - ``score``:   ``{"type": "score", "instructions": "...",
                          "criteria": ["level 0", "level 1", ...]}``

    Returns
    -------
    dict
        The full system-one response body: ``{"model", "answers", "usage"}``.
        ``answers`` is keyed by question name; each answer carries a ``type``
        field (``"noul"``, ``"choice"`` or ``"score"``).

    Raises
    ------
    JevError
        If the request fails (auth, network, HTTP error) or the server
        returns a non-JSON body.
    """
    try:
        resp = requests.post(
            JEV_SYSTEM_ONE_URL,
            headers={
                "Authorization": f"Bearer {OPENCODE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": JEV_MODEL,
                "state": state,
                "questions": questions,
            },
            timeout=60,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        detail = ""
        if exc.response is not None:
            detail = f": {exc.response.text}"
        raise JevError(f"Jev request failed: {exc}{detail}") from exc
    try:
        return resp.json()
    except ValueError as exc:
        raise JevError(f"Jev returned a non-JSON response: {exc}") from exc