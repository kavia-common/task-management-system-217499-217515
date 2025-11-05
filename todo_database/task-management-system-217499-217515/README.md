# task-management-system-217499-217515

Backend (todo_database) - FastAPI over SQLite
- Location: task-management-system-217499-217515/todo_database
- Database file: myapp.db (SQLite)

Run locally:
1) cd task-management-system-217499-217515/todo_database
2) python3 -m venv .venv && source .venv/bin/activate    # optional but recommended
3) pip install -r requirements.txt
4) uvicorn app:app --host 0.0.0.0 --port 5001 --reload

API endpoints:
- GET     /api/health
- GET     /api/tasks
- POST    /api/tasks
- PUT     /api/tasks/{id}
- PATCH   /api/tasks/{id}/complete?complete=true|false
- DELETE  /api/tasks/{id}

Docs:
- Swagger UI: http://localhost:5001/docs
- ReDoc:      http://localhost:5001/redoc

CORS:
- Allows http://localhost:3000 for development.
