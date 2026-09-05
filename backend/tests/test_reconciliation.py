from decimal import Decimal
from app.engines.reconciliation import reconcile_batch

def test_reconcile_batch_level_1():
    transactions = [{'id': 'tx1', 'gateway_transaction_id': 'gw1', 'amount': 100.0}]
    settlements = [{'id': 's1', 'gateway_transaction_id': 'gw1', 'amount': 100.0}]
    result = reconcile_batch(transactions, settlements)
    assert result.matched == 1
    assert result.items[0].match_level == 1
    assert result.items[0].discrepancy == 0.0
    assert result.unmatched == 0
    assert result.match_rate == 1.0

def test_reconcile_batch_level_2():
    transactions = [{'id': 'tx1', 'order_id': 'ord1', 'amount': 100.0}]
    settlements = [{'id': 's1', 'order_id': 'ord1', 'amount': 100.0}]
    result = reconcile_batch(transactions, settlements)
    assert result.matched == 1
    assert result.items[0].match_level == 2

def test_reconcile_unmatched():
    transactions = [{'id': 'tx1', 'gateway_transaction_id': 'gw1', 'amount': 100.0}]
    settlements = [{'id': 's1', 'gateway_transaction_id': 'gw2', 'amount': 100.0}]
    result = reconcile_batch(transactions, settlements)
    assert result.matched == 0
    assert result.unmatched == 1
    assert result.match_rate == 0.0

def test_reconcile_discrepancy():
    transactions = [{'id': 'tx1', 'gateway_transaction_id': 'gw1', 'amount': 12500.0}]
    settlements = [{'id': 's1', 'gateway_transaction_id': 'gw1', 'amount': 11950.0}]
    result = reconcile_batch(transactions, settlements)
    assert result.partial == 1
    assert abs(abs(result.items[0].discrepancy) - 550.0) < 0.01
    assert result.match_rate > 0.0

def test_reconcile_mixed_batch():
    transactions = [
        {'id': 'tx1', 'gateway_transaction_id': 'gw1', 'amount': 100.0},
        {'id': 'tx2', 'gateway_transaction_id': 'gw2', 'amount': 200.0},
        {'id': 'tx3', 'gateway_transaction_id': 'gw3', 'amount': 300.0}
    ]
    settlements = [
        {'id': 's1', 'gateway_transaction_id': 'gw1', 'amount': 100.0},
        {'id': 's2', 'gateway_transaction_id': 'gw2', 'amount': 200.0}
    ]
    result = reconcile_batch(transactions, settlements)
    assert result.matched == 2
    assert result.unmatched == 0
    assert result.match_rate == 1.0

def test_reconcile_large_mismatch_exception():
    transactions = [{'id': 'tx1', 'gateway_transaction_id': 'gw1', 'amount': 100000.0}]
    settlements = [{'id': 's1', 'gateway_transaction_id': 'gw1', 'amount': 22000.0}]
    result = reconcile_batch(transactions, settlements)
    assert len(result.exceptions) > 0
    assert abs(abs(result.exceptions[0].discrepancy) - 78000.0) < 0.01
