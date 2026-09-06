# FLOOD-X — Security Guide

> Security posture documentation for the prototype.  
> **Current status:** Prototype — not production-hardened. See hardening steps below.

---

## Current Security Posture

| Control | Status | Notes |
|---------|--------|-------|
| Authentication | ❌ Not implemented | Scaffolding present (`python-jose`, `passlib`) |
| Authorization | ❌ Not implemented | All endpoints are open |
| HTTPS/TLS | ⚠️ Nginx-only | TLS termination at reverse proxy |
| CORS | ✅ Configured | Restricted origins via `CORS_ORIGINS` env |
| Secret key | ⚠️ Dev default | Must change `SECRET_KEY` before production |
| SQL injection | ✅ Protected | SQLAlchemy ORM parameterized queries |
| XSS | ✅ Protected | React escapes all dynamic content |
| CSRF | ✅ N/A | Stateless API, no cookie sessions |
| Secrets in code | ✅ Clean | `.env.example` only, `.gitignore` excludes `.env` |
| Dependency audit | ⚠️ Manual | No automated vulnerability scanning yet |
| Rate limiting | ❌ Not implemented | Add via `slowapi` for production |

---

## Secrets Management

### What must NEVER be committed to git:
- `.env` (excluded by `.gitignore`)
- Database passwords
- API keys (IMD, CMWSSB)
- `SECRET_KEY`

### Current safe defaults (development only):
```
SECRET_KEY=dev-secret-key-change-in-production   ← CHANGE THIS
POSTGRES_PASSWORD=floodx_dev_password            ← CHANGE THIS
```

### Generating a production secret key:
```bash
openssl rand -hex 32
# → paste into .env: SECRET_KEY=<result>
```

---

## Production Hardening Checklist

```
[ ] Set SECRET_KEY to cryptographically random 32-byte hex
[ ] Set POSTGRES_PASSWORD to strong password (min 20 chars)
[ ] Set CORS_ORIGINS to exact production domain only
[ ] Enable HTTPS via Let's Encrypt (Certbot + nginx)
[ ] Add JWT authentication to all API routes
[ ] Add rate limiting via slowapi (pip install slowapi)
[ ] Enable PostgreSQL SSL mode
[ ] Run: pip install safety && safety check  (dependency audit)
[ ] Configure nginx security headers:
    X-Content-Type-Options: nosniff
    X-Frame-Options: DENY
    Content-Security-Policy: default-src 'self'
[ ] Enable structured access logging
[ ] Set up secrets rotation policy
```

---

## Adding JWT Authentication

Scaffolding is already in `requirements.txt`:

```python
# backend/app/routers/auth.py (to be implemented)
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## Data Privacy

FLOOD-X does not collect, store, or transmit:
- Personal information
- Device identifiers
- User location data (the map shows flood zones, not user positions)
- Usage analytics

The prototype does not have user accounts. All data is about infrastructure state, not individuals.

---

## Responsible Disclosure

This is a prototype submission for SIH 2026. Known security limitations are disclosed in this document. If deployed in production for emergency management, a full security audit by a qualified penetration tester is **required** before go-live.
