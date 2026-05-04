"""An email sender that keeps messages instead of sending them.

Production swaps this for the real email provider. Pass ``outbox_dir`` to also
write each message to a ``.txt`` file, which is handy when running the CLI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Send one email."""


class StubEmailSender(EmailSender):
    def __init__(self, outbox_dir: Path | None = None) -> None:
        self.sent: list[EmailMessage] = []
        self._outbox_dir = outbox_dir

    def send(self, message: EmailMessage) -> None:
        self.sent.append(message)
        if self._outbox_dir is not None:
            self._outbox_dir.mkdir(parents=True, exist_ok=True)
            path = self._outbox_dir / f"{len(self.sent):04d}.txt"
            path.write_text(
                f"To: {message.to}\nSubject: {message.subject}\n\n{message.body}\n",
                encoding="utf-8",
            )
