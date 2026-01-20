import json
from typing import Dict, Any
from src.scoring import calculate_risk_score, determine_risk_level

def generate_report(state: Dict[str, Any]) -> str:
    """
    Generate a styled HTML report from analysis results
    """
    agent_outputs = state.get("agent_outputs", {})
    relationship = state.get("relationship", {})
    
    # Aggregate features
    all_features = {}
    for agent_name, agent_data in agent_outputs.items():
        if isinstance(agent_data, dict):
            features = agent_data.get("features", {})
            if features:
                all_features.update(features)
    
    # Calculate risk
    risk_score = calculate_risk_score(all_features)
    risk_level = determine_risk_level(risk_score)
    
    # Risk color based on user's requested scheme: 1-3 Red, 4-7 Yellow, 8-10 Green
    if risk_score < 4.0:
        risk_color = "#ef4444"  # Red
    elif risk_score < 8.0:
        risk_color = "#f59e0b"  # Yellow
    else:
        risk_color = "#10b981"  # Green
    
    # Extract metadata
    legal_data = agent_outputs.get("Legal", {})
    contract_type = legal_data.get("contract_type", {}).get("primary", "General Agreement")
    legality = legal_data.get("contract_legality", {}).get("status", "Valid")
    
    # Agent icons
    agent_icons = {
        "Legal": "fa-scale-balanced",
        "Finance": "fa-money-bill-trend-up",
        "Compliance": "fa-shield-check",
        "Operations": "fa-gears",
        "Security": "fa-user-shield"
    }

    # Build HTML
    html = f"""
    <div class="report-wrapper" style="color: #1f2937;">
        <!-- Header Section -->
        <div class="report-top-bar" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;">
            <div>
                <h2 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 8px;">Contract Intelligence Report</h2>
                <div style="display: flex; gap: 8px;">
                    <span style="background: #eef2ff; color: #4f46e5; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Type: {contract_type}</span>
                    <span style="background: #ecfdf5; color: #059669; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Status: {legality}</span>
                    { f"<span style='background: #f3f4f6; color: #374151; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;'>{relationship.get('relationship', 'New').replace('_', ' ')}</span>" if relationship else "" }
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.7rem; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">Composite Risk</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: {risk_color};">{risk_level.upper()}</div>
                <div style="font-size: 0.85rem; color: #4b5563; margin-bottom: 8px;">Score: {risk_score:.1f}/10</div>
                <a href="/download_report/{state.get('doc_id', 'unknown')}" target="_blank" 
                   style="display: inline-block; padding: 4px 12px; background: #10b981; color: white; text-decoration: none; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                    <i class="fa-solid fa-download"></i> Download Report
                </a>
            </div>
        </div>

        <!-- Dashboard Grid -->
        <div class="agent-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 32px;">
    """

    # Add agent summary cards
    for agent in ["Legal", "Finance", "Compliance", "Operations", "Security"]:
        data = agent_outputs.get(agent, {})
        a_score = data.get("risk_score", 0)
        threshold = data.get("features", {}).get("threshold_value")
        threshold_html = ""
        if threshold and threshold != "none" and threshold != "N/A":
            threshold_html = f"""
                <div style="margin-top: 8px; font-size: 0.75rem; font-weight: 600; color: #475569; background: #f1f5f9; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    Threshold: {threshold}
                </div>
            """
            
        # Color based on score: 1-3 Red, 4-7 Yellow, 8-10 Green
        a_color = "#ef4444" if a_score < 4 else "#f59e0b" if a_score < 8 else "#10b981"
        icon = agent_icons.get(agent, "fa-user-robot")

        html += f"""
            <div class="agent-summary-card" style="background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; transition: all 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 32px; height: 32px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #4f46e5;">
                            <i class="fa-solid {icon}"></i>
                        </div>
                        <span style="font-weight: 600; font-size: 0.95rem;">{agent}</span>
                    </div>
                    <div style="font-weight: 700; color: {a_color}; background: {a_color}15; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem;">
                        Risk: {a_score}/10
                    </div>
                </div>
                <p style="font-size: 0.85rem; color: #4b5563; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 0;">
                    {data.get('analysis', 'No analysis available for this agent.')}
                </p>
                {threshold_html}
            </div>
        """

    html += """
        </div>

        <!-- Detailed Agent Deep Dive -->
        <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
            <i class="fa-solid fa-list-check" style="color: #4f46e5;"></i> Agent Deep Dive
        </h3>
        
        <div class="agent-details-container" style="display: flex; flex-direction: column; gap: 24px;">
    """

    for agent in ["Legal", "Finance", "Compliance", "Operations", "Security"]:
        data = agent_outputs.get(agent, {})
        if not data:
            continue
        
        analysis = data.get("analysis", "No detailed analysis provided.")
        clauses = data.get("extracted_clauses", {})
        icon = agent_icons.get(agent, "fa-user-robot")

        html += f"""
            <div class="agent-detail-block" style="border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fff;">
                <div style="background: #f9fafb; padding: 12px 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="font-weight: 600; color: #111827; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid {icon}" style="color: #4f46e5; font-size: 0.9rem;"></i> {agent} Assessment
                    </h4>
                    <span style="font-size: 0.75rem; color: #6b7280; font-weight: 500;">ID: AI-{agent[:3].upper()}-{state.get('doc_id', 'xxxx')[:4]}</span>
                </div>
                <div style="padding: 20px;">
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #374151; margin-bottom: 20px;">
                        {analysis}
                    </div>
        """
        
        # Add extracted clauses if they exist
        if clauses:
            html += """
                    <div style="background: #f8fafc; border-radius: 8px; padding: 16px;">
                        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                            <i class="fa-solid fa-quote-left"></i> Key Extracted Clauses
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
            """
            for key, val in clauses.items():
                if val and val != "None":
                    html += f"""
                            <div style="font-size: 0.85rem; border-left: 2px solid #e2e8f0; padding-left: 12px;">
                                <div style="font-weight: 600; color: #475569; margin-bottom: 4px;">{key.replace('_', ' ').title()}</div>
                                <div style="color: #64748b; font-style: italic; font-family: 'Inter', serif;">"{val}"</div>
                            </div>
                    """
            html += """
                        </div>
                    </div>
            """

        html += """
                </div>
            </div>
        """

    html += f"""
        </div>
        <!-- Hidden Doc ID for Feedback -->
        <div id="report-doc-id" data-id="{state.get('doc_id', 'unknown')}" style="display: none;"></div>
    </div>
    """
    
    return html
