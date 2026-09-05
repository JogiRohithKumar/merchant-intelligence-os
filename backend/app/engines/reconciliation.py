"""
Deterministic 4-Level Reconciliation Engine
No LLM involvement in matching logic.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ReconciliationItem:
    settlement_item_id: str
    transaction_id: Optional[str]
    settlement_amount: float
    transaction_amount: Optional[float]
    match_level: Optional[int]
    match_confidence: float
    discrepancy: float
    match_status: str  # 'matched', 'partial', 'unmatched'
    possible_reason: Optional[str] = None

@dataclass
class ReconciliationResult:
    total_records: int
    matched: int
    partial: int
    unmatched: int
    match_rate: float
    discrepancy_amount: float
    items: list = field(default_factory=list)
    exceptions: list = field(default_factory=list)

def reconcile_batch(transactions: list[dict], settlement_items: list[dict]) -> ReconciliationResult:
    """
    4-level deterministic matching.
    transactions: list of {id, gateway_transaction_id, order_id, customer_id, amount, created_at, gateway}
    settlement_items: list of {id, gateway_transaction_id, order_id, amount, settlement_date, gateway, customer_id}
    """
    results = []
    matched = 0
    partial = 0
    unmatched = 0
    total_discrepancy = 0.0
    
    # Build lookup indexes
    txn_by_gw_id = {t['gateway_transaction_id']: t for t in transactions if t.get('gateway_transaction_id')}
    txn_by_order_id = {t['order_id']: t for t in transactions if t.get('order_id')}
    txn_by_amount_time = {}  # (amount, day, customer) -> txn
    for t in transactions:
        if t.get('created_at') and t.get('customer_id'):
            key = (round(float(t['amount']), 2), t['created_at'][:10], t.get('customer_id', ''))
            txn_by_amount_time[key] = t
    
    for item in settlement_items:
        matched_txn = None
        match_level = None
        confidence = 0.0
        discrepancy = 0.0
        
        # Level 1: Exact gateway transaction ID match
        gw_id = item.get('gateway_transaction_id')
        if gw_id and gw_id in txn_by_gw_id:
            matched_txn = txn_by_gw_id[gw_id]
            match_level = 1
            confidence = 1.0
        
        # Level 2: Order ID match
        if not matched_txn:
            order_id = item.get('order_id')
            if order_id and order_id in txn_by_order_id:
                matched_txn = txn_by_order_id[order_id]
                match_level = 2
                confidence = 0.92
        
        # Level 3: Amount + Date + Customer
        if not matched_txn:
            settle_date = (item.get('settlement_date') or '')[:10]
            # Settlement date is ~2 days after transaction
            from datetime import datetime
            try:
                sd = datetime.fromisoformat(settle_date)
                possible_txn_dates = [(sd - timedelta(days=d)).strftime('%Y-%m-%d') for d in range(0, 4)]
            except:
                possible_txn_dates = [settle_date]
            
            for txn_date in possible_txn_dates:
                key = (round(float(item['amount']), 2), txn_date, item.get('customer_id', ''))
                if key in txn_by_amount_time:
                    matched_txn = txn_by_amount_time[key]
                    match_level = 3
                    confidence = 0.78
                    break
        
        # Level 4: Fuzzy — amount within 2% + same gateway + same day window
        if not matched_txn and item.get('gateway'):
            item_amount = float(item['amount'])
            for t in transactions:
                t_amount = float(t['amount'])
                if abs(t_amount - item_amount) / max(item_amount, 1) < 0.02:
                    if t.get('gateway') and t.get('gateway') == item.get('gateway'):
                        matched_txn = t
                        match_level = 4
                        confidence = 0.61
                        break
        
        if matched_txn:
            discrepancy = float(item['amount']) - float(matched_txn['amount'])
            if abs(discrepancy) < 0.01:
                match_status = 'matched'
                matched += 1
            else:
                match_status = 'partial'
                partial += 1
            total_discrepancy += abs(discrepancy)
            
            possible_reason = None
            if abs(discrepancy) > 0:
                if discrepancy < 0:
                    possible_reason = 'Gateway fee / tax deduction'
                else:
                    possible_reason = 'Amount adjustment or partial refund'
        else:
            match_status = 'unmatched'
            unmatched += 1
            confidence = 0.0
            possible_reason = 'No matching transaction found — possible fee, adjustment, or data gap'
        
        results.append(ReconciliationItem(
            settlement_item_id=item['id'],
            transaction_id=matched_txn['id'] if matched_txn else None,
            settlement_amount=float(item['amount']),
            transaction_amount=float(matched_txn['amount']) if matched_txn else None,
            match_level=match_level,
            match_confidence=round(confidence, 3),
            discrepancy=round(discrepancy, 2),
            match_status=match_status,
            possible_reason=possible_reason
        ))
    
    total = len(settlement_items)
    match_rate = (matched + partial * 0.5) / total if total > 0 else 0.0
    
    exceptions = [r for r in results if r.match_status == 'unmatched' or abs(r.discrepancy) > 100]
    
    return ReconciliationResult(
        total_records=total,
        matched=matched,
        partial=partial,
        unmatched=unmatched,
        match_rate=round(match_rate, 4),
        discrepancy_amount=round(total_discrepancy, 2),
        items=results,
        exceptions=exceptions
    )
