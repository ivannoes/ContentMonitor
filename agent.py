"""OpenAI agent using the Responses API with function-calling.

The agent automatically discovers every tool registered in
``tools.TOOL_REGISTRY`` and exposes them to the model.  The tool-calling
loop follows the official OpenAI guidelines:

    1.  Send the user prompt together with the tool definitions.
    2.  If the model responds with ``function_call`` output items,
        execute the matching tool and append a ``function_call_output``.
    3.  Send the updated input list back to the model.
    4.  Repeat until the model produces a text response.
"""

import json
import sys
from typing import Any

from openai import AuthenticationError, OpenAI, RateLimitError

from config import OPENAI_API_KEY, OPENAI_MODEL, validate_openai_credentials
from tools import TOOL_REGISTRY


class ContentAgent:
    """Thin wrapper around the OpenAI Responses API with tool support."""

    def __init__(self) -> None:
        validate_openai_credentials()
        self._client = OpenAI(api_key=OPENAI_API_KEY)
        self._model = OPENAI_MODEL

        # Build a name → tool lookup from the registry
        self._tools_by_name: dict[str, Any] = {
            tool.name: tool for tool in TOOL_REGISTRY
        }

        # Schemas sent to the API
        self._tool_schemas: list[dict] = [
            tool.schema for tool in TOOL_REGISTRY
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, user_prompt: str, instructions: str = "") -> str:
        """Execute the agent loop and return the final text answer.

        Parameters
        ----------
        user_prompt:
            The user's natural-language request.
        instructions:
            Optional system-level instructions for the model.

        Returns
        -------
        str
            The model's final text output after all tool calls have been
            resolved.
        """
        input_list: list[dict] = [
            {"role": "user", "content": user_prompt},
        ]

        while True:
            print(
                "\n⏳ Waiting for model response...",
                file=sys.stderr,
                flush=True,
            )
            try:
                response = self._client.responses.create(
                    model=self._model,
                    instructions=instructions,
                    tools=self._tool_schemas,
                    input=input_list,
                )
            except AuthenticationError:
                return "Error: Invalid API key. Check your .env file."
            except RateLimitError:
                return (
                    "Error: No OpenAI credits remaining. "
                    "Add billing at https://platform.openai.com/account/billing."
                )
            except Exception as exc:
                return f"Error: An unexpected error occurred: {exc}"

            # Append the model's output items to the running input
            input_list += response.output

            # Check if the model made any function calls
            function_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                # No more tool calls – return the final text
                return response.output_text

            # Execute each tool and append results
            for i, call in enumerate(function_calls, 1):
                tool = self._tools_by_name.get(call.name)
                if tool is None:
                    print(
                        f"  ⚠ Unknown tool: {call.name}",
                        file=sys.stderr,
                        flush=True,
                    )
                    result = json.dumps(
                        {"error": f"Unknown tool: {call.name}"}
                    )
                else:
                    print(
                        f"  🔧 [{i}/{len(function_calls)}] Running {call.name}...",
                        file=sys.stderr,
                        flush=True,
                    )
                    args = json.loads(call.arguments)
                    result = tool.execute(**args)
                    print(
                        f"  ✅ {call.name} done.",
                        file=sys.stderr,
                        flush=True,
                    )

                input_list.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": result,
                    }
                )

    # ------------------------------------------------------------------
    # Summarization (no tools)
    # ------------------------------------------------------------------

    def summarize(self, text: str, instructions: str = "") -> str:
        """Send *text* to the model for summarization only (no tools).

        Parameters
        ----------
        text:
            The content to summarize (e.g. CSV data).
        instructions:
            Optional system-level instructions for the model.

        Returns
        -------
        str
            The model's text response.
        """
        print(
            "\n\u23f3 Waiting for model summary...",
            file=sys.stderr,
            flush=True,
        )
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=instructions,
                input=[{"role": "user", "content": text}],
            )
        except AuthenticationError:
            return "Error: Invalid API key. Check your .env file."
        except RateLimitError:
            return (
                "Error: No OpenAI credits remaining. "
                "Add billing at https://platform.openai.com/account/billing."
            )
        except Exception as exc:
            return f"Error: An unexpected error occurred: {exc}"

        return response.output_text

