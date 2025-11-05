# Dev Connectivity Checks

- FastAPI runs with:
  uvicorn app:app --host 0.0.0.0 --port 5001 --reload
- Uses local SQLite DB file: myapp.db in this folder.
- CORS: Allows http://localhost:3000 (frontend dev).

Manual curl checks:
- Health:
  curl -s http://localhost:5001/api/health | jq .

- List:
  curl -s http://localhost:5001/api/tasks | jq .

- Create:
  curl -s -X POST http://localhost:5001/api/tasks \
    -H 'Content-Type: application/json' \
    -d '{"title":"Sample","description":"From curl"}' | jq .

- Replace (PUT):
  curl -s -X PUT http://localhost:5001/api/tasks/1 \
    -H 'Content-Type: application/json' \
    -d '{"title":"Updated","description":"Edited","completed":true}' | jq .

- Toggle complete (PATCH):
  curl -s -X PATCH 'http://localhost:5001/api/tasks/1/complete?complete=false' | jq .

- Delete:
  curl -s -X DELETE -i http://localhost:5001/api/tasks/1
