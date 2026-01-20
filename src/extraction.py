import os
from typing import Dict, List, Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Initialize
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
model = SentenceTransformer('all-MiniLM-L6-v2')
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "contracts-v2")

# Agent-specific query topics
AGENT_TOPICS = {
    "Legal": ["indemnity", "liability", "termination", "governing law", "warranties"],
    "Finance": ["payment terms", "pricing", "fees", "renewal", "penalties"],
    "Compliance": ["data protection", "GDPR", "privacy", "audit rights", "compliance"],
    "Operations": ["SLA", "uptime", "service level", "support", "maintenance"],
    "Security": ["security", "encryption", "disaster recovery", "backup", "access control"]
}

def extract_clauses(doc_id: str, plan: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract relevant clauses for each agent using semantic search
    """
    index = pc.Index(INDEX_NAME)
    results = {}
    
    for agent_name, topics in AGENT_TOPICS.items():
        print(f"Extracting clauses for {agent_name}...")
        agent_clauses = []
        
        for topic in topics:
            # Generate query embedding
            query_embedding = model.encode(topic).tolist()
            
            # Search Pinecone
            search_results = index.query(
                vector=query_embedding,
                filter={"doc_id": doc_id},
                top_k=3,
                include_metadata=True
            )
            
            # Collect matches
            for match in search_results.matches:
                if match.score > 0.0:  # Only include relevant matches
                    agent_clauses.append({
                        "topic": topic,
                        "text": match.metadata.get("text", ""),
                        "score": match.score
                    })
        
        # Remove duplicates and sort by score
        unique_clauses = []
        seen_texts = set()
        for clause in sorted(agent_clauses, key=lambda x: x["score"], reverse=True):
            if clause["text"] not in seen_texts:
                unique_clauses.append(clause)
                seen_texts.add(clause["text"])
        
        results[agent_name] = unique_clauses[:5]  # Top 5 clauses per agent
        print(f"  > Found {len(results[agent_name])} chunks for {agent_name}")
        if results[agent_name]:
            print(f"  > Top score: {results[agent_name][0]['score']}")
    
    return results
