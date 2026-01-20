from typing import Dict, TypedDict, Annotated, List, Any, Optional
import operator
from langgraph.graph import StateGraph, END
import os

# Import modules
from src.ingestion import ingest_document, parse_document
from src.extraction import extract_clauses
from src.agents.definitions import analyze_clauses
from src.reporting import generate_report
from src.history_manager import HistoryManager

# Define state
class OrchestratorState(TypedDict):
    file_path: str
    doc_id: str
    text_summary: str
    plan: Dict[str, Any]
    extracted_clauses: Dict[str, Any]
    agent_outputs: Annotated[Dict[str, Any], operator.ior]
    final_report: str
    history_context: Optional[List[Dict[str, Any]]]
    relationship: Optional[Dict[str, Any]]

# ---- NODES ----

def ingestion_node(state: OrchestratorState):
    """Ingest document and register in history"""
    print(f"--- Ingesting: {state['file_path']} ---")
    
    # Initialize History Manager
    hm = HistoryManager()
    
    # Detect relationship
    relationship = hm.detect_relationship(state['file_path'])
    
    # Register upload
    hm_result = hm.register_upload(state['file_path'], state['doc_id'])
    
    filename = os.path.basename(state['file_path'])
    original_name = filename.split('_', 1)[1] if '_' in filename else filename
    history_context = hm.get_document_context(original_name)
    
    result = ingest_document(state["file_path"], doc_id=state.get("doc_id"))
    text = parse_document(state["file_path"])
    
    return {
        "doc_id": result["doc_id"],
        "text_summary": text,
        "history_context": history_context,
        "relationship": relationship
    }

def planning_node(state: OrchestratorState):
    """Planning step (simplified)"""
    print("--- Planning ---")
    # Simplified plan - just pass through
    plan = {"agents": ["Legal", "Finance", "Compliance", "Operations", "Security"]}
    return {"plan": plan}

def extraction_node(state: OrchestratorState):
    """Extract relevant clauses for each agent"""
    print("--- Extracting Clauses ---")
    clauses = extract_clauses(state["doc_id"], state["plan"])
    return {"extracted_clauses": clauses}

def legal_agent_node(state: OrchestratorState):
    """Legal agent analysis"""
    print("--- Agent: Legal ---")
    clauses = state["extracted_clauses"].get("Legal", [])
    output = analyze_clauses("Legal", clauses)
    return {"agent_outputs": {"Legal": output}}

def finance_agent_node(state: OrchestratorState):
    """Finance agent analysis"""
    print("--- Agent: Finance ---")
    clauses = state["extracted_clauses"].get("Finance", [])
    output = analyze_clauses("Finance", clauses)
    return {"agent_outputs": {"Finance": output}}

def compliance_agent_node(state: OrchestratorState):
    """Compliance agent analysis"""
    print("--- Agent: Compliance ---")
    clauses = state["extracted_clauses"].get("Compliance", [])
    output = analyze_clauses("Compliance", clauses)
    return {"agent_outputs": {"Compliance": output}}

def operations_agent_node(state: OrchestratorState):
    """Operations agent analysis"""
    print("--- Agent: Operations ---")
    clauses = state["extracted_clauses"].get("Operations", [])
    output = analyze_clauses("Operations", clauses)
    return {"agent_outputs": {"Operations": output}}

def security_agent_node(state: OrchestratorState):
    """Security agent analysis"""
    print("--- Agent: Security ---")
    clauses = state["extracted_clauses"].get("Security", [])
    output = analyze_clauses("Security", clauses)
    return {"agent_outputs": {"Security": output}}

def reporting_node(state: OrchestratorState):
    """Generate final HTML report"""
    print("--- Generating Report ---")
    report = generate_report(state)
    return {"final_report": report}

# ---- BUILD GRAPH ----
workflow = StateGraph(OrchestratorState)

workflow.add_node("ingest", ingestion_node)
workflow.add_node("planning", planning_node)
workflow.add_node("extract", extraction_node)
workflow.add_node("legal", legal_agent_node)
workflow.add_node("finance", finance_agent_node)
workflow.add_node("compliance", compliance_agent_node)
workflow.add_node("operations", operations_agent_node)
workflow.add_node("security", security_agent_node)
workflow.add_node("report", reporting_node)

workflow.set_entry_point("ingest")
workflow.add_edge("ingest", "planning")
workflow.add_edge("planning", "extract")

# Fan out to all agents
workflow.add_edge("extract", "legal")
workflow.add_edge("extract", "finance")
workflow.add_edge("extract", "compliance")
workflow.add_edge("extract", "operations")
workflow.add_edge("extract", "security")

# Fan in to report
workflow.add_edge("legal", "report")
workflow.add_edge("finance", "report")
workflow.add_edge("compliance", "report")
workflow.add_edge("operations", "report")
workflow.add_edge("security", "report")

workflow.add_edge("report", END)

# Compile without debug to avoid langchain.debug error
app = workflow.compile(debug=False)
