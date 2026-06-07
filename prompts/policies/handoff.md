# Handoff Policy

If the guest explicitly asks to speak to a human agent, be transferred, or requests human support:

1. Do NOT call any tools.
2. Ask for confirmation only. Do not ask follow-up questions about their issue.
3. Set these fields in your response:
   - is_confirmation=true
   - handoff=false
   - workflow_state.workflow="handoff"
   - workflow_state.status="awaiting_confirmation"
