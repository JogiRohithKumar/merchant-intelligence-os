import pytest
from app.agents.supervisor.agent import SupervisorAgent
from app.schemas.state import AgentName

def test_r01_revenue_decline(db_session):
    supervisor = SupervisorAgent(db_session, 'merchant-bharat-001')
    query = "My revenue dropped 20% this month. Find the reasons and recover whatever you safely can."
    intents = supervisor._detect_intents(query)
    selected, rejected, plan = supervisor._plan_agents(intents)
    
    assert AgentName.FINANCE in selected
    assert AgentName.RISK in selected
    assert AgentName.GROWTH in selected
    assert AgentName.RECOVERY in selected
    assert len(rejected) == 0

def test_r02_chargeback_spike(db_session):
    supervisor = SupervisorAgent(db_session, 'merchant-bharat-001')
    query = "My chargebacks suddenly increased."
    intents = supervisor._detect_intents(query)
    selected, rejected, plan = supervisor._plan_agents(intents)
    
    assert AgentName.RISK in selected
    assert AgentName.FINANCE in selected
    assert AgentName.RECOVERY not in selected
    assert AgentName.GROWTH not in selected
    assert AgentName.RECOVERY in rejected
    assert AgentName.GROWTH in rejected

def test_r03_payment_failures(db_session):
    supervisor = SupervisorAgent(db_session, 'merchant-bharat-001')
    query = "My payment failure rate increased."
    intents = supervisor._detect_intents(query)
    selected, rejected, plan = supervisor._plan_agents(intents)
    
    assert AgentName.RECOVERY in selected
    assert AgentName.RISK in selected
    assert AgentName.FINANCE not in selected
    assert AgentName.GROWTH not in selected
    assert AgentName.FINANCE in rejected
    assert AgentName.GROWTH in rejected

def test_r04_settlement_mismatch(db_session):
    supervisor = SupervisorAgent(db_session, 'merchant-bharat-001')
    query = "My settlement amount doesn't match my expected amount."
    intents = supervisor._detect_intents(query)
    selected, rejected, plan = supervisor._plan_agents(intents)
    
    assert AgentName.FINANCE in selected
    assert AgentName.RISK not in selected
    assert AgentName.RECOVERY not in selected
    assert AgentName.GROWTH not in selected
    assert AgentName.RISK in rejected
    assert AgentName.RECOVERY in rejected

def test_r05_product_conversion_decline(db_session):
    supervisor = SupervisorAgent(db_session, 'merchant-bharat-001')
    query = "Product X conversion is falling. How can I improve it?"
    intents = supervisor._detect_intents(query)
    selected, rejected, plan = supervisor._plan_agents(intents)
    
    assert AgentName.GROWTH in selected
    assert AgentName.RISK not in selected
    assert AgentName.RECOVERY not in selected
    assert AgentName.RISK in rejected
    assert AgentName.RECOVERY in rejected
