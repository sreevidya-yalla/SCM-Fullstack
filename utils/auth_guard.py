from utils.jwt_utility import (
    verify_access_token, verify_refresh_token,
    create_access_token
)

async def require_user(request):
    access = request.session.get("access_token")
    refresh = request.session.get("refresh_token")

    # 1) Access token valid
    if access:
        payload = verify_access_token(access)
        if payload:
            return {
                "email": payload["sub"],
                "new_access": None
            }

    # 2) If access expired → try refresh
    if refresh:
        ref_payload = verify_refresh_token(refresh)
        if ref_payload:
            email = ref_payload["sub"]
            new_access = create_access_token({"sub": email})

            # update session
            request.session["access_token"] = new_access

            return {
                "email": email,
                "new_access": new_access
            }

    # 3) Both expired
    return None

