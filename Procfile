# FLOOD-X — Render/Railway/Heroku Procfile
# ==========================================
# Render uses render.yaml (preferred). This Procfile is a fallback.
#
# $PORT is injected automatically by Render at runtime.
# --workers 1 is appropriate for the free tier (512 MB RAM).
# Increase to 2-4 workers on paid tiers.
web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
