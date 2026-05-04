from novastack_orders.utils.ids import SequentialIds, random_reference


def test_sequential_ids_are_zero_padded():
    ids = SequentialIds(prefix="ORD", start=41)
    assert [ids.next(), ids.next()] == ["ORD-000041", "ORD-000042"]


def test_random_references_differ():
    assert random_reference() != random_reference()
