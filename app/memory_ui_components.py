import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from typing import List, Dict, Any, Tuple
from datetime import datetime
from expense_manager.memory_system import memory_system

def generate_conversation_card(conversation: Dict[str, Any]) -> str:
    """Generate a beautiful conversation card in HTML/Markdown format."""
    
    # Get query type emoji and styling
    type_emojis = {
        "simple": "🔍",
        "multi_step": "🔄", 
        "complex": "🧠"
    }
    
    type_colors = {
        "simple": "#e3f2fd",      # Light blue
        "multi_step": "#fff3e0",  # Light orange  
        "complex": "#f3e5f5"      # Light purple
    }
    
    query_type = conversation.get("query_type", "simple")
    emoji = type_emojis.get(query_type, "❓")
    bg_color = type_colors.get(query_type, "#f5f5f5")
    
    # Format timestamp
    timestamp = conversation.get("timestamp", "")
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
        except:
            time_str = timestamp
            date_str = ""
    else:
        time_str = "Unknown"
        date_str = ""
    
    # Get query and result
    query = conversation.get("query", "N/A")
    result = conversation.get("result", "N/A")
    
    # Check for multi-step execution
    metadata = conversation.get("metadata", {})
    is_multi_step = metadata.get("is_multi_step", False)
    step_results = metadata.get("step_results", [])
    
    # Build the card HTML
    card_html = f"""
    <div style="
        border: 1px solid #ddd; 
        border-radius: 12px; 
        padding: 16px; 
        margin: 8px 0; 
        background: linear-gradient(135deg, {bg_color} 0%, #ffffff 100%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2em;">{emoji}</span>
                <span style="font-weight: bold; color: #333;">{query_type.replace('_', ' ').title()}</span>
            </div>
            <div style="font-size: 0.85em; color: #666;">
                {date_str} at {time_str}
            </div>
        </div>
        
        <div style="margin-bottom: 12px;">
            <div style="font-weight: bold; color: #2c3e50; margin-bottom: 6px;">❓ Query:</div>
            <div style="background: #f8f9fa; padding: 8px; border-radius: 6px; border-left: 3px solid #3498db;">
                {query}
            </div>
        </div>
        
        <div style="margin-bottom: 12px;">
            <div style="font-weight: bold; color: #2c3e50; margin-bottom: 6px;">💬 Response:</div>
            <div style="background: #f8f9fa; padding: 8px; border-radius: 6px; border-left: 3px solid #27ae60;">
                {result[:300]}{'...' if len(result) > 300 else ''}
            </div>
        </div>
    """
    
    # Add multi-step execution details if available
    if is_multi_step and step_results:
        card_html += f"""
        <div style="margin-top: 12px; padding: 8px; background: #fff8e1; border-radius: 6px; border: 1px solid #ffcc02;">
            <div style="font-weight: bold; color: #f57c00; margin-bottom: 6px;">
                🔄 Multi-Step Execution ({len(step_results)} steps)
            </div>
            <div style="font-size: 0.9em;">
        """
        
        for i, step in enumerate(step_results[:3], 1):  # Show first 3 steps
            step_desc = step.get("step_description", "Unknown step")
            success = step.get("success", True)
            status_icon = "✅" if success else "❌"
            card_html += f"<div style='margin: 2px 0;'>{status_icon} Step {i}: {step_desc}</div>"
        
        if len(step_results) > 3:
            card_html += f"<div style='margin: 2px 0; font-style: italic; color: #666;'>... and {len(step_results) - 3} more steps</div>"
        
        card_html += "</div></div>"
    
    card_html += "</div>"
    
    return card_html

def generate_memory_display(limit: int = 10, 
                          query_type_filter: str = "All",
                          search_term: str = "") -> str:
    """Generate the complete memory display."""
    
    # Apply filters
    conversations = []
    
    if search_term.strip():
        conversations = memory_system.search_conversations(search_term)
    else:
        filter_type = None if query_type_filter == "All" else query_type_filter.lower().replace(" ", "_")
        conversations = memory_system.get_conversations(
            limit=limit,
            session_only=False,
            query_type=filter_type
        )
    
    if not conversations:
        return """
        <div style="text-align: center; padding: 40px; color: #666;">
            <h3>🧠 No conversations found</h3>
            <p>Start asking questions to build up your conversation history!</p>
        </div>
        """
    
    # Generate memory stats
    stats = memory_system.get_memory_stats()
    
    # Header with stats
    header = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 16px; 
                border-radius: 12px; 
                margin-bottom: 16px;
                text-align: center;">
        <h2 style="margin: 0;">🧠 Conversation Memory</h2>
        <div style="display: flex; justify-content: space-around; margin-top: 12px; font-size: 0.9em;">
            <div><strong>{stats['total_conversations']}</strong><br/>Total Chats</div>
            <div><strong>{stats['session_conversations']}</strong><br/>This Session</div>
            <div><strong>{stats['query_type_breakdown'].get('complex', 0)}</strong><br/>Complex Queries</div>
        </div>
    </div>
    """
    
    # Generate conversation cards
    cards_html = ""
    for conversation in conversations:
        cards_html += generate_conversation_card(conversation)
    
    return header + cards_html

def export_memory_handler(format_choice: str, session_only: bool) -> Tuple[str, str]:
    """Handle memory export."""
    try:
        content = memory_system.export_conversations(
            format=format_choice.lower(),
            session_only=session_only
        )
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_suffix = "_session" if session_only else "_all"
        filename = f"expense_assistant_memory{session_suffix}_{timestamp}.{format_choice.lower()}"
        
        return content, filename
    
    except Exception as e:
        return f"❌ Export failed: {e}", "error.txt"

def clear_memory_handler(session_only: bool) -> Tuple[str, str]:
    """Handle memory clearing."""
    try:
        memory_system.clear_memory(session_only=session_only)
        
        if session_only:
            message = "✅ Current session memory cleared!"
        else:
            message = "✅ All memory cleared!"
        
        # Return updated display
        updated_display = generate_memory_display()
        return message, updated_display
    
    except Exception as e:
        return f"❌ Clear failed: {e}", generate_memory_display()

def search_memory_handler(search_term: str, 
                         query_type_filter: str, 
                         result_limit: int) -> str:
    """Handle memory search and filtering."""
    return generate_memory_display(
        limit=result_limit,
        query_type_filter=query_type_filter,
        search_term=search_term
    ) 