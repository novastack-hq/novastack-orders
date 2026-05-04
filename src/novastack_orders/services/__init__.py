"""Use cases: checkout, order management, notifications.

Services orchestrate the domain and the adapters. They receive their adapters
in ``__init__`` (dependency injection), so tests pass in fakes.
"""
