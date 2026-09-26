"""
This module is responsible for handling 'Building Messages List' , 'Formating Messages' , 'Extracting , Appending Messages/Tool Results/History' and will return a List of dictionaries containing {role:content} items.
"""

from enum  import Enum
from typing import Any


class Roles(Enum):
    SYSTEM='system'
    USER='user'
    ASSISTANT='assistant'

from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: Any = None
    raw: dict | None = None   # if set, this wins — used to pass through pre-built dicts untouched

    def to_dict(self) -> dict:
        return self.raw if self.raw is not None else {"role": self.role, "content": self.content}

    @staticmethod
    def system(content: str) -> "Message":
        return Message(role="system", content=content)
    @staticmethod
    def user(content: str) -> "Message":
        return Message(role="user", content=content)

    @staticmethod
    def assistant(content: str) -> "Message":
        return Message(role="assistant", content=content)

    @staticmethod
    def from_dict(d: dict) -> "Message":
        return Message(role=d.get("role", ""), raw=d)

    #? Serialized in agent run()
    @staticmethod
    def serialize(messages: list["Message"]) -> list[dict]:
        return [m.to_dict() for m in messages]
