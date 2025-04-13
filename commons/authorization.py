from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer
import os
import jwt
from datetime import datetime

SECRET_KEY = os.getenv("SECRET_KEY")
SECURITY_ALGORITHM = os.getenv("SECURITY_ALGORITHM")

reusable_oauth2 = HTTPBearer(
    scheme_name='Authorization'
)

def get_token(authorization: HTTPBearer = Depends(reusable_oauth2)):
    return authorization.credentials

def verify_token(token: str = Security(get_token)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], verify=True)
        return payload
    except jwt.ExpiredSignatureError:
        error_response = {
            "message": "Token has expired",
            "error_key": "token_expired",
            "statusCode": 401
        }
        raise HTTPException(status_code=401, detail=error_response)
    except jwt.InvalidTokenError:
        error_response = {
            "message": "Invalid token",
            "error_key": "token_expired",
            "statusCode": 401
        }
        raise HTTPException(status_code=401, detail=error_response)
    
    