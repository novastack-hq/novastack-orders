"""Adapters: the outside world (storage, payments, email) behind interfaces.

Services depend on the abstract classes in each ``base``/``gateway`` module,
never on a concrete adapter, so tests can swap in fakes. See ADR 0003.
"""
