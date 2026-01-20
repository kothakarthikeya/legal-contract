import requests
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

AGENT_PROMPTS = {
    "Legal": """
    You are a Legal Agent. Review the contract clauses for risk mitigation and enforceability.
    
    Output JSON MUST include these exact keys:
    {{
        "agent": "Legal",
        "analysis": "Text summary...",
        "risk_score": (1-10 estimation based on text),
        "contract_legality": {{ "status": "Legally Valid" or "Not a Contract", "desc": "..." }},
        "contract_type": {{ "primary": "Type...", "secondary": "..." }},
        "features": {{
            "indemnity_cap_present": boolean,
            "liability_cap_present": boolean,
            "threshold_value": "string or number (e.g. $10,000)",
            "termination_for_convenience": boolean,
            "consequential_damages_waiver": boolean,
            "governing_law_match": boolean
        }},
        "extracted_clauses": {{
            "indemnity": "text snippet...",
            "liability": "text snippet...",
            "termination": "text snippet..."
        }}
    }}
    
    Clauses provided:
    {clauses}
    """,
    
    "Finance": """
    You are a Finance Agent. Review the contract clauses for financial obligations.
    
    Output JSON MUST include these exact keys:
    {{
        "agent": "Finance",
        "analysis": "Text summary...",
        "risk_score": (1-10),
        "financial_details": {{ "payment_terms": "..." }},
        "features": {{
            "payment_terms_days": number,
            "late_payment_penalty_present": boolean,
            "threshold_value": "string or number (e.g. $5,000)",
            "auto_renewal": boolean,
            "price_increase_cap_present": boolean
        }},
        "extracted_clauses": {{
            "payment_terms": "text snippet...",
            "pricing": "text snippet..."
        }}
    }}
    
    Clauses provided:
    {clauses}
    """,
    
    "Compliance": """
    You are a Compliance Agent. Review for data protection and security.
    
    Output JSON MUST include these exact keys:
    {{
        "agent": "Compliance",
        "analysis": "Text summary...",
        "risk_score": (1-10),
        "features": {{
            "gdpr_addressed": boolean,
            "audit_rights_missing": boolean
        }},
         "extracted_clauses": {{
            "data_protection": "text snippet...",
            "security": "text snippet..."
        }}
    }}
    
    Clauses provided:
    {clauses}
    """,
    
    "Operations": """
    You are an Operations Agent. Review for SLA and support.
    
    Output JSON MUST include these exact keys:
    {{
        "agent": "Operations",
        "analysis": "Text summary...",
        "risk_score": (1-10),
        "features": {{
            "sla_uptime": number (e.g. 99.9),
            "maintenance_window_defined": boolean
        }},
         "extracted_clauses": {{
            "sla": "text snippet...",
            "support": "text snippet..."
        }}
    }}
    
    Clauses provided:
    {clauses}
    """,
    
    "Security": """
    You are a Security Agent. Review for IT security, disaster recovery, and data protection measures.
    
    Output JSON MUST include these exact keys:
    {{
        "agent": "Security",
        "analysis": "Text summary...",
        "risk_score": (1-10),
        "features": {{
            "encryption_at_rest": boolean,
            "encryption_in_transit": boolean,
            "disaster_recovery_plan": boolean,
            "multi_factor_auth": boolean
        }},
        "extracted_clauses": {{
            "security_measures": "text snippet...",
            "disaster_recovery": "text snippet..."
        }}
    }}
    
    Clauses provided:
    {clauses}
    """
}

def analyze_clauses(agent_name: str, clauses: List[Dict]) -> Dict[str, Any]:
    """
    Perform agent-specific analysis on extracted clauses
    """
    if not clauses:
        return {
            "agent": agent_name,
            "error": "No clauses provided for analysis",
            "risk_score": 0,
            "analysis": "No clauses available for analysis",
            "features": {}
        }
        
    prompt_template = AGENT_PROMPTS.get(agent_name, "Analyze these clauses: {clauses}")
    
    # Format clauses into a string
    clauses_text = "\n---\n".join([f"Source ({c.get('topic')}):\n{c['text']}" for c in clauses])
    
    # Fallback models
    fallback_models = [
        "meta-llama/Llama-3.2-1B-Instruct",
        "google/gemma-2-2b-it",
        "mistralai/Mistral-7B-Instruct-v0.3"
    ]
    
    try:
        content = None
        last_error = None
        
        for model_id in fallback_models:
            try:
                headers = {
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": f"You are a {agent_name} contract analysis agent. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt_template.format(clauses=clauses_text)}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1500
                }
                
                response = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(f"✓ {agent_name} analysis completed with {model_id}")
                    break
                else:
                    last_error = f"Model {model_id} failed: {response.status_code}"
                    continue
                    
            except Exception as e:
                last_error = str(e)
                continue
        
        if not content:
            return {
                "agent": agent_name,
                "error": last_error,
                "analysis": f"Analysis failed: {last_error}",
                "risk_score": 5,
                "features": {}
            }
            
        # Parse JSON response
        import re
        clean_content = content.strip()
        
        # Try to find JSON in code blocks
        json_code_block = re.search(r'```json\s*(.*?)\s*```', clean_content, re.DOTALL)
        if json_code_block:
            clean_content = json_code_block.group(1)
        else:
            json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
            if json_match:
                clean_content = json_match.group(0)

        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as je:
            return {
                "agent": agent_name,
                "analysis": f"AI returned data but JSON parsing failed. Snippet: {clean_content[:200]}",
                "risk_score": 5,
                "error": str(je),
                "features": {}
            }

    except Exception as e:
        return {
            "agent": agent_name,
            "error": str(e),
            "analysis": f"System error during analysis: {str(e)}",
            "risk_score": 0,
            "features": {}
        }
