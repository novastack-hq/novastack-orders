from novastack_orders.adapters.notifications.email_stub import (
    EmailMessage,
    StubEmailSender,
)


def test_keeps_sent_messages():
    sender = StubEmailSender()
    sender.send(EmailMessage("a@example.com", "Hi", "Body"))
    assert sender.sent[0].subject == "Hi"


def test_can_write_messages_to_an_outbox_folder(tmp_path):
    sender = StubEmailSender(outbox_dir=tmp_path / "outbox")
    sender.send(EmailMessage("a@example.com", "Hi", "Body"))
    written = (tmp_path / "outbox" / "0001.txt").read_text(encoding="utf-8")
    assert written.startswith("To: a@example.com")
