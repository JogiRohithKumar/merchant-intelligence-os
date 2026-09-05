"""
RAG Knowledge Base for Financial Context
Provides financial knowledge to agents for explanation and context.
NEVER used for arithmetic, reconciliation, or fraud scoring.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class KnowledgeChunk:
    content: str
    source: str
    relevance_score: float

# Embedded knowledge base (no external DB needed for demo)
KNOWLEDGE_BASE = [
    {
        "id": "k001",
        "source": "payment_failure_guide",
        "title": "Payment Failure Recovery Strategies",
        "content": "gateway_timeout failures have 72% recovery rate when retried within 24 hours. network_error failures typically recover within 1-2 retries. card_declined may require customer notification to update payment method. insufficient_funds recovery improves significantly after salary credit dates (1st and 10th of month)."
    },
    {
        "id": "k002", 
        "source": "chargeback_guide",
        "title": "Chargeback Reason Codes and Evidence Requirements",
        "content": "Reason code 4853: Cardholder dispute - item not received. Requires delivery proof, tracking ID, customer communication records. Reason code 4855: Non-receipt of merchandise. Provide shipping confirmation, order logs. Reason code 10.4: Other fraud. Requires IP logs, device fingerprint, order details, customer verification records."
    },
    {
        "id": "k003",
        "source": "reconciliation_guide",
        "title": "Settlement Reconciliation Rules",
        "content": "Settlement discrepancies commonly arise from: (1) Gateway fees (2% standard, 2.5% international), (2) Chargeback holds, (3) Refund deductions, (4) Tax (GST 18% on fees), (5) Timing differences. Settlements typically arrive T+2 business days. Amount within 0.5% is considered matched."
    },
    {
        "id": "k004",
        "source": "fraud_indicators",
        "title": "Fraud Detection Indicators",
        "content": "High-risk signals: Multiple transactions from same IP within 1 hour, new device + high amount + high-risk country, historical chargebacks >= 2, refund rate > 20%, velocity breach (>5 txns/hour). Segment B customers show 4.7% chargeback rate vs 0.8% baseline — investigate for abuse ring."
    },
    {
        "id": "k005",
        "source": "recovery_best_practices",
        "title": "Payment Recovery Best Practices",
        "content": "Retry payments within 24-48 hours for gateway timeouts. Space retries: Day 1, Day 3, Day 7. Send customer notification for card-related failures. Use smart retry — avoid retrying on weekends for B2B. Maximum 2 retry attempts before escalating to manual recovery. Promise-to-pay tracking improves B2B recovery by 35%."
    },
    {
        "id": "k006",
        "source": "cash_forecast_methodology",
        "title": "Cash Forecasting Methodology",
        "content": "Cash forecast uses Holt's double exponential smoothing: captures both level and trend. 30-day forecast with 90% confidence interval. Key inputs: historical inflows (settlement credits), outflows (refunds, fees, chargebacks), settlement schedule. Seasonal adjustments applied for festival periods (Diwali, year-end)."
    },
    {
        "id": "k007",
        "source": "pci_compliance",
        "title": "PCI DSS Compliance Notes",
        "content": "Never store CVV/CVC. Card numbers must be tokenized. PAN data must be encrypted at rest. All payment logs must include masked card numbers only. Fraud data must be retained for 12 months for dispute evidence. DPDP Act compliance required for Indian customer data."
    },
    {
        "id": "k008",
        "source": "segment_analysis",
        "title": "Customer Segment Risk Profiles",
        "content": "Segment A (15% of customers): Premium customers, low risk (0.05 risk score), high AOV. Segment B (20%): Higher chargeback rate (4.7%), possible abuse ring involvement, requires enhanced monitoring. Segment C (40%): Standard customers, baseline metrics. Segment D (25%): Inactive customers with low recent purchase history, good reactivation targets."
    }
]

_chroma_client = None
_collection = None

def _get_collection():
    """Get or create ChromaDB collection. Falls back to in-memory keyword search."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from app.core.config import settings
        _chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        _collection = _chroma_client.get_or_create_collection('financial_knowledge')
        if _collection.count() == 0:
            _collection.add(
                documents=[k['content'] for k in KNOWLEDGE_BASE],
                metadatas=[{'source': k['source'], 'title': k['title']} for k in KNOWLEDGE_BASE],
                ids=[k['id'] for k in KNOWLEDGE_BASE]
            )
            logger.info('ChromaDB collection seeded with financial knowledge.')
        return _collection
    except Exception as e:
        logger.warning(f'ChromaDB not available ({e}), using in-memory keyword search.')
        return None

def query_knowledge(question: str, n_results: int = 3) -> list[KnowledgeChunk]:
    """Query the knowledge base for relevant context."""
    collection = _get_collection()
    
    if collection is not None:
        try:
            results = collection.query(query_texts=[question], n_results=n_results)
            chunks = []
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i] if results.get('distances') else 0.5
                relevance = max(0, 1 - dist)
                chunks.append(KnowledgeChunk(content=doc, source=meta.get('source', 'unknown'), relevance_score=round(relevance, 3)))
            return chunks
        except Exception as e:
            logger.warning(f'ChromaDB query failed: {e}, falling back to keyword search')
    
    # Fallback: keyword-based search
    question_lower = question.lower()
    keywords = question_lower.split()
    scored = []
    for kb in KNOWLEDGE_BASE:
        content_lower = kb['content'].lower()
        score = sum(1 for kw in keywords if kw in content_lower) / max(len(keywords), 1)
        if score > 0:
            scored.append((score, kb))
    scored.sort(reverse=True)
    return [
        KnowledgeChunk(content=kb['content'], source=kb['source'], relevance_score=round(score, 3))
        for score, kb in scored[:n_results]
    ]
