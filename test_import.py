import sys
sys.path.insert(0, r'd:\Projects\InsightIQ – Enterprise Customer Intelligence Platform\backend')
from app.main import app
routes = [{'path': r.path, 'methods': list(r.methods)} for r in app.routes]
import json
print(json.dumps(routes[:5], indent=2))