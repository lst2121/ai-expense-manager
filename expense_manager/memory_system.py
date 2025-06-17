import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

class EnhancedMemorySystem:
    """
    Enhanced memory system for the AI Expense Assistant.
    
    Features:
    - Rich conversation storage with metadata
    - Multi-step execution tracking
    - Search and filtering capabilities
    - Persistent storage across sessions
    - Export functionality
    """
    
    def __init__(self, memory_file: str = "data/conversation_memory.json"):
        self.memory_file = memory_file
        self.conversations = []
        self.current_session_id = self._generate_session_id()
        self.load_memory()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_conversation(self, 
                        query: str, 
                        result: str, 
                        analysis_metadata: Dict[str, Any] = None) -> None:
        """
        Add a conversation to memory with rich metadata.
        
        Args:
            query: User's original query
            result: Assistant's response
            analysis_metadata: Additional data from the analysis (multi-step info, etc.)
        """
        conversation = {
            "id": f"conv_{len(self.conversations) + 1}",
            "session_id": self.current_session_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "result": result,
            "metadata": analysis_metadata or {},
            "query_type": self._classify_query_type(analysis_metadata),
            "execution_time": analysis_metadata.get("execution_time", 0) if analysis_metadata else 0
        }
        
        self.conversations.append(conversation)
        self.save_memory()
    
    def _classify_query_type(self, metadata: Dict[str, Any]) -> str:
        """Classify the type of query for visual indicators."""
        if not metadata:
            return "simple"
        
        if metadata.get("is_multi_step", False):
            step_count = len(metadata.get("step_results", []))
            if step_count >= 3:
                return "complex"
            else:
                return "multi_step"
        
        return "simple"
    
    def get_conversations(self, 
                         limit: int = None, 
                         session_only: bool = False,
                         query_type: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve conversations with optional filtering.
        
        Args:
            limit: Maximum number of conversations to return
            session_only: Only return conversations from current session
            query_type: Filter by query type (simple, multi_step, complex)
        """
        filtered = self.conversations
        
        if session_only:
            filtered = [c for c in filtered if c["session_id"] == self.current_session_id]
        
        if query_type:
            filtered = [c for c in filtered if c["query_type"] == query_type]
        
        # Sort by timestamp (newest first)
        filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def search_conversations(self, search_term: str) -> List[Dict[str, Any]]:
        """Search conversations by query content."""
        search_term = search_term.lower()
        results = []
        
        for conv in self.conversations:
            if (search_term in conv["query"].lower() or 
                search_term in conv["result"].lower()):
                results.append(conv)
        
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system."""
        total_conversations = len(self.conversations)
        session_conversations = len([c for c in self.conversations 
                                   if c["session_id"] == self.current_session_id])
        
        query_types = {}
        for conv in self.conversations:
            qtype = conv["query_type"]
            query_types[qtype] = query_types.get(qtype, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "session_conversations": session_conversations,
            "query_type_breakdown": query_types,
            "current_session": self.current_session_id,
            "memory_file": self.memory_file
        }
    
    def export_conversations(self, 
                           format: str = "json", 
                           session_only: bool = False) -> str:
        """
        Export conversations in various formats.
        
        Args:
            format: Export format (json, markdown, csv)
            session_only: Only export current session
        """
        conversations = self.get_conversations(session_only=session_only)
        
        if format == "json":
            return json.dumps(conversations, indent=2)
        
        elif format == "markdown":
            md_content = f"# AI Expense Assistant - Conversation History\n\n"
            md_content += f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            md_content += f"**Total Conversations:** {len(conversations)}\n\n"
            
            for conv in conversations:
                md_content += f"## 🗣️ Query {conv['id']}\n"
                md_content += f"**Time:** {conv['timestamp']}\n"
                md_content += f"**Type:** {conv['query_type']} {self._get_type_emoji(conv['query_type'])}\n\n"
                md_content += f"**Question:** {conv['query']}\n\n"
                md_content += f"**Answer:**\n{conv['result']}\n\n"
                
                if conv['metadata'].get('is_multi_step'):
                    steps = conv['metadata'].get('step_results', [])
                    md_content += f"**Execution Steps:** {len(steps)} steps\n"
                    for i, step in enumerate(steps, 1):
                        md_content += f"  {i}. {step.get('step_description', 'Unknown step')}\n"
                
                md_content += "---\n\n"
            
            return md_content
        
        elif format == "csv":
            data = []
            for conv in conversations:
                data.append({
                    "ID": conv["id"],
                    "Timestamp": conv["timestamp"],
                    "Query": conv["query"],
                    "Result": conv["result"][:100] + "..." if len(conv["result"]) > 100 else conv["result"],
                    "Type": conv["query_type"],
                    "Multi_Step": conv["metadata"].get("is_multi_step", False)
                })
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        
        return json.dumps(conversations, indent=2)
    
    def _get_type_emoji(self, query_type: str) -> str:
        """Get emoji for query type."""
        emojis = {
            "simple": "🔍",
            "multi_step": "🔄", 
            "complex": "🧠"
        }
        return emojis.get(query_type, "❓")
    
    def clear_memory(self, session_only: bool = False) -> None:
        """Clear memory (current session or all)."""
        if session_only:
            self.conversations = [c for c in self.conversations 
                                if c["session_id"] != self.current_session_id]
        else:
            self.conversations = []
        
        self.save_memory()
    
    def save_memory(self) -> None:
        """Save memory to file."""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save memory: {e}")
    
    def load_memory(self) -> None:
        """Load memory from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.conversations = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load memory: {e}")
            self.conversations = []

# Global memory instance
memory_system = EnhancedMemorySystem() 