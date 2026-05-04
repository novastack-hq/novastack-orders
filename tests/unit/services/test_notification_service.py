from novastack_orders.adapters.notifications.email_stub import StubEmailSender
from novastack_orders.services.notification_service import NotificationService
from tests.factories import make_basket


def test_confirmation_goes_to_the_customer(checkout, outbox, customers):
    checkout.checkout("C400", make_basket(("D01", 1)), "tok_visa")
    message = outbox.sent[0]
    assert message.to == customers.get("C400").email
    assert "Thanks for your order" in message.body


def test_cancellation_email(checkout, customers):
    sender = StubEmailSender()
    order = checkout.checkout("C100", make_basket(("D01", 1)), "tok_visa")
    NotificationService(sender).order_cancelled(customers.get("C100"), order)
    assert sender.sent[0].subject == f"Order {order.order_id} cancelled"
