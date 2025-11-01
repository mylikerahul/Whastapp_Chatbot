"""
HOTFIX: Critical bug fixes for intent_service.py
Copy-paste this into your intent_service.py
"""

# Replace _is_real_estate_query method:

def _is_real_estate_query(self, message: str) -> bool:
    """FIXED: Real estate query detection"""
    message_lower = message.lower()
    
    # Technical keywords = NOT real estate
    technical_keywords = [
        "report", "dashboard", "data", "analytics", "kpi",
        "ai report", "campaign report", "analysis",
        "salesforce", "crm", "system", "ticket", "issue",
        "error", "not working", "down", "sync", "login"
    ]
    
    if any(keyword in message_lower for keyword in technical_keywords):
        return False  # Technical query
    
    # Only real estate if EXPLICIT property intent
    property_patterns = [
        r'(?:buy|purchase|looking for|want|show me)\s+(?:villa|apartment|property)',
        r'(?:2|3|4|5)\s*(?:bed|bedroom).*(?:villa|apartment)',
        r'view(ing)?\s+property'
    ]
    
    return any(re.search(p, message_lower) for p in property_patterns)


# Add at start of _handle_confirmation:

async def _handle_confirmation(...):
    """FIXED: Handle new issues during confirmation"""
    
    # Detect if NEW issue (not confirmation)
    issue_keywords = ["salesforce", "dashboard", "login", "password", 
                     "website", "laptop", "error", "not working"]
    
    has_new_issue = sum(1 for k in issue_keywords if k in message_text.lower()) >= 2
    
    is_confirm = any(w in message_text.lower() for w in ['yes', 'confirm', 'ok'])
    is_cancel = any(w in message_text.lower() for w in ['no', 'cancel'])
    
    # If NEW issue detected
    if has_new_issue and not is_confirm and not is_cancel:
        response_service.clear_pending_ticket(user_phone)
        await gallabox_service.send_text_message(
            user_phone, 
            "Got it! Let me help with this new issue."
        )
        # Signal to reprocess
        return {"action": "new_issue", "reprocess": True}
    
    # Continue normal flow...