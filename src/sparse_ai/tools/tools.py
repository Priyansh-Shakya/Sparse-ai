"""
This module is responsible for handling - creating , formatting , serializing and extracting tools for System Prompt.
"""

import inspect
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


class Tool():
    """
    Framework representation of a callable tool.

    A Tool wraps a user-defined function without changing its actual
    execution signature. The original function remains the single source
    of truth for the tool's name and parameters.

    Tool metadata is derived from the function and optional decorators.
    For example, ``@approval_request`` attaches approval information to
    the function without adding parameters or wrapping the function.

    Function docstring pattern::

        function_name:
            Description of what the function does.

            Args:
                arg1 (type): Description of the argument.
                arg2 (type): Description of the argument.
                arg3 (type): Description of the argument.

    Attributes:
        func (callable):
            The original user-defined function. It is not replaced by a
            wrapper and remains directly callable by the framework.

        name (str):
            The function's name, obtained directly from ``func.__name__``.
            This is the single source of truth for the tool name.

        approval_instruction (str | None):
            Optional human-approval instruction attached by the
            ``@approval_request`` decorator. ``None`` means the tool does
            not have an approval request configured.

    Approval requests:

        A tool can be marked as requiring human approval before execution::

            @approval_request()
            def execute_sql(query: str):
                ...

        An optional instruction can provide additional context for the
        approval request::

            @approval_request(
                "Explain exactly what rows this deletes."
            )
            def delete_rows(query: str):
                ...

        The decorator only attaches metadata to the original function.
        It does not modify the function's signature, add fake parameters,
        or alter its execution behavior.

    The Tool class can therefore independently obtain:

        - the callable from ``func``
        - the function name from ``func.__name__``
        - the parameters/signature from the original function
        - approval metadata from ``func._approval_instruction``

    This separation allows tool metadata to be serialized for an LLM
    without coupling the model-facing schema to the function's execution
    interface.
    """
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

        self.needs_approval = getattr(
            func,
            "_needs_approval",
            False,
        )

        self.approval_instruction = getattr(
            func,
            "_approval_instruction",
            None,
        )

    def _type_to_schema(self, annotation):

        # -------------------------------------------------
        # No annotation
        # -------------------------------------------------

        if annotation is inspect.Parameter.empty:
            return {
                "type": "string"
            }

        # -------------------------------------------------
        # Any
        # -------------------------------------------------

        if annotation is Any:
            return {}

        # -------------------------------------------------
        # Basic types
        # -------------------------------------------------

        if annotation is str:
            return {
                "type": "string"
            }

        if annotation is int:
            return {
                "type": "integer"
            }

        if annotation is float:
            return {
                "type": "number"
            }

        if annotation is bool:
            return {
                "type": "boolean"
            }

        # -------------------------------------------------
        # list / list[T]
        # -------------------------------------------------

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is list:

            item_type = args[0] if args else Any

            return {
                "type": "array",
                "items": self._type_to_schema(item_type),
            }

        # -------------------------------------------------
        # dict / dict[K, V]
        # -------------------------------------------------

        if origin is dict:

            return {
                "type": "object"
            }

        # -------------------------------------------------
        # Optional / Union
        # -------------------------------------------------

        if origin is Union:

            non_none = [
                arg
                for arg in args
                if arg is not type(None)
            ]

            if len(non_none) == 1:
                return self._type_to_schema(non_none[0])

            return {
                "anyOf": [
                    self._type_to_schema(arg)
                    for arg in non_none
                ]
            }

        # -------------------------------------------------
        # Python 3.10+ union: str | None
        # -------------------------------------------------

        import types

        if origin is types.UnionType:

            non_none = [
                arg
                for arg in args
                if arg is not type(None)
            ]

            if len(non_none) == 1:
                return self._type_to_schema(non_none[0])

            return {
                "anyOf": [
                    self._type_to_schema(arg)
                    for arg in non_none
                ]
            }

        # -------------------------------------------------
        # Fallback
        # -------------------------------------------------

        return {
            "type": "string"
        }

    def create_tool_definition(self):

        signature = inspect.signature(self.func)

        # IMPORTANT:
        # Resolve forward/string annotations.
        try:
            type_hints = get_type_hints(self.func)
        except Exception:
            type_hints = {}

        docstring = inspect.getdoc(self.func) or ""

        description = docstring

        if self.approval_instruction:
            description += (
                "\n\nBefore execution, "
                "provide an approval explanation."
            )

        parameters = {}
        required = []

        for name, parameter in signature.parameters.items():

            # ---------------------------------------------
            # Don't expose *args / **kwargs
            # ---------------------------------------------

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            # ---------------------------------------------
            # IMPORTANT:
            # Use resolved type hint instead of
            # parameter.annotation
            # ---------------------------------------------

            annotation = type_hints.get(
                name,
                parameter.annotation,
            )

            parameters[name] = self._type_to_schema(
                annotation
            )

            if parameter.default is inspect.Parameter.empty:
                required.append(name)

        # ---------------------------------------------
        # Approval field exists ONLY in LLM schema
        # ---------------------------------------------

        if self.needs_approval:

            parameters["__approval_request__"] = {
                "type": "string",
                "description": self.approval_instruction,
            }

            required.append("__approval_request__")

        return {
            "name": self.name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        }


    async def execute(self, **kwargs):

        # Schema-only field.
        # Never pass this to the user's function.
        kwargs.pop(
            "__approval_request__",
            None,
        )

        if inspect.iscoroutinefunction(self.func):
            exe =  await self.func(**kwargs)
            print("===================================================================================================\nTool Executed:", exe)
            return exe
        exe= self.func(**kwargs)
        print("===================================================================================================\nTool Executed:", exe)
        return exe

    @staticmethod
    def serialize_tool(tools: list):
        return [
            tool.create_tool_definition()
            for tool in tools
        ]