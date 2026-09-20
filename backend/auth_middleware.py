"""
Real Cedar authorization via Amazon Verified Permissions (MIGRATION_PLAN.md Phase 3).

Replaces the previous hand-rolled Cedar-shaped string parser. Policies live in
cedar/*.cedar, loaded into AVP by scripts/bootstrap.sh — nothing is embedded here.
"""
import logging
from functools import wraps

from fastapi import Request, HTTPException

try:
    from . import config  # imported as backend.auth_middleware
except ImportError:
    import config  # run standalone / imported flat

logger = logging.getLogger("chronolab.auth")

# Route (method, path template) -> Cedar action ID. The path template comes from
# request.scope["route"].path (set by Starlette once the route is matched), so this
# stays in sync with server.py without server.py needing to pass anything explicitly.
ROUTE_ACTION_MAP = {
    ("GET", "/api/records/{patient_id}"): "ViewRecords",
    ("GET", "/api/medications/{patient_id}"): "ViewRecords",
    ("POST", "/api/medications/nlp"): "AddMedication",
    ("GET", "/api/insights/{patient_id}"): "ViewInsights",
    ("GET", "/api/export/fhir/{patient_id}"): "ExportFHIR",
    ("POST", "/api/chat"): "ViewInsights",
}

ACTION_TYPE = "ChronoLab::Action"
RESOURCE_TYPE = "ChronoLab::Record"


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    return auth_header[len("Bearer "):]


def _extract_target_patient_id(kwargs: dict) -> str | None:
    if "patient_id" in kwargs:
        return kwargs["patient_id"]
    payload = kwargs.get("payload")
    return getattr(payload, "patient_id", None) if payload is not None else None


def evaluate_authorization(token: str, action_id: str, target_patient_id: str | None) -> dict:
    """Calls AVP IsAuthorizedWithToken. Returns the raw AVP response dict."""
    client = config.get_real_aws_client("verifiedpermissions")

    resource_id = target_patient_id or "unknown"
    response = client.is_authorized_with_token(
        policyStoreId=config.get_avp_policy_store_id(),
        identityToken=token,
        action={"actionType": ACTION_TYPE, "actionId": action_id},
        resource={"entityType": RESOURCE_TYPE, "entityId": resource_id},
        entities={
            "entityList": [
                {
                    "identifier": {"entityType": RESOURCE_TYPE, "entityId": resource_id},
                    "attributes": {"patient_id": {"string": resource_id}},
                }
            ]
        },
    )
    return response


def requires_auth(resource_type: str = "PatientRecord"):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = _extract_bearer_token(request)

            route_path = request.scope["route"].path
            action_id = ROUTE_ACTION_MAP.get((request.method, route_path))
            if action_id is None:
                logger.warning(f"No Cedar action mapped for {request.method} {route_path}; denying by default")
                raise HTTPException(status_code=403, detail={"decision": "DENY", "reason": "unmapped route"})

            target_patient_id = _extract_target_patient_id(kwargs)

            try:
                decision = evaluate_authorization(token, action_id, target_patient_id)
            except Exception as e:
                logger.warning(f"AVP authorization call failed for {action_id} on {route_path}: {e}")
                raise HTTPException(status_code=403, detail={"decision": "DENY", "reason": "authorization check failed"})

            if decision.get("decision") != "ALLOW":
                determining_policies = [p.get("policyId") for p in decision.get("determiningPolicies", [])]
                logger.warning(
                    f"AVP denied {action_id} on {route_path} "
                    f"(determining policies: {determining_policies})"
                )
                raise HTTPException(
                    status_code=403,
                    detail={"decision": "DENY", "determining_policies": determining_policies},
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
