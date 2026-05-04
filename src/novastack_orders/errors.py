"""The project's exception hierarchy.

Catch the most specific error you can handle. Everything raised on purpose by
this package derives from :class:`NovastackError`, so callers such as the CLI
can catch that one class at the boundary and show a friendly message.
"""


class NovastackError(Exception):
    """Base class for all errors raised deliberately by NovaStack Orders."""


class ValidationError(NovastackError):
    """Input data is malformed or breaks a business rule."""


class NotFoundError(NovastackError):
    """A requested record (menu item, customer, order) does not exist."""


class OrderStateError(NovastackError):
    """An order cannot move to the requested status from its current one."""


class PaymentError(NovastackError):
    """The payment provider declined or failed to process a charge."""


class ConfigError(NovastackError):
    """A configuration file is missing or contains invalid values."""
