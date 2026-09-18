import re
from fastapi import Request, HTTPException
from functools import wraps

# Mock Cedar Policy
# In a real AWS environment, this would be deployed to Amazon Verified Permissions.
# Since LocalStack currently 500s on AVP, we parse the Cedar syntax locally to demonstrate the concept.
CEDAR_POLICY = """
permit (
    principal,
    action,
    resource
)
when { principal.role == "doctor" || principal.id == resource.owner_id };
"""

def evaluate_cedar_policy(principal: dict, action: str, resource: dict) -> bool:
    """
    Evaluates the basic Cedar policy string.
    If principal is a doctor, or principal id matches resource owner id, permit.
    Otherwise deny.
    """
    # Extremely basic mock parser for hackathon demonstration
    if "principal.role == \"doctor\"" in CEDAR_POLICY and principal.get("role") == "doctor":
        return True
    if "principal.id == resource.owner_id" in CEDAR_POLICY and principal.get("id") == resource.get("owner_id"):
        return True
        
    return False

def requires_auth(resource_type="PatientRecord"):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # In a real app, principal comes from JWT token. 
            # For hackathon demo, we read it from headers (e.g. X-User-Role, X-User-Id).
            user_id = request.headers.get("X-User-Id", "unknown")
            user_role = request.headers.get("X-User-Role", "patient")
            
            principal = {"id": user_id, "role": user_role}
            
            # Extract target resource owner from path params (e.g., patient_id)
            target_owner_id = kwargs.get("patient_id")
            resource = {"type": resource_type, "owner_id": target_owner_id}
            
            action = request.method
            
            is_permitted = evaluate_cedar_policy(principal, action, resource)
            
            if not is_permitted:
                raise HTTPException(status_code=403, detail="Forbidden by Cedar Policy")
                
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
