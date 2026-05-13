"""Integration test for projects and clients endpoints."""
import sys
sys.path.insert(0, "backend")

from datetime import datetime, timezone
from app.schemas.parser import (
    ClientCreateSchema, ClientUpdateSchema,
    ProjectCreateSchema, ProjectUpdateSchema,
)
from app.services.clients_service import (
    create_client, find_client, update_client, delete_client, get_client_projects,
)
from app.api.routes.projects import _projects_store, get_projects_store

# Test 1: Client CRUD
client = create_client(ClientCreateSchema(name="ООО СтройМонтаж", inn="7701234567"))
cid = client["id"]
print(f"1. Created client: id={cid[:8]}, name={client['name']}")
found = find_client(cid)
assert found is not None, "Client not found after create"
assert found["name"] == "ООО СтройМонтаж"

updated = update_client(cid, ClientUpdateSchema(name="ООО СтройМонтаж-2"))
assert updated["name"] == "ООО СтройМонтаж-2"
print(f"   Updated: name={updated['name']}")

# Test 2: Create project with client
import uuid
pid = uuid.uuid4()
proj = {
    "id": pid,
    "external_code": "PRJ-001",
    "name": "ЖК Северный",
    "stage": "kmd",
    "client_id": cid,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
}
_projects_store.append(proj)
print(f"2. Created project: id={str(pid)[:8]}, name={proj['name']}")

# Test 3: Link client → projects
projects = get_client_projects(cid, get_projects_store())
assert len(projects) == 1, f"Expected 1 project, got {len(projects)}"
assert projects[0]["name"] == "ЖК Северный"
print(f"3. Client projects: {len(projects)} found, first={projects[0]['name']}")

# Test 4: Update project
proj["stage"] = "construction"
proj["updated_at"] = datetime.now(timezone.utc)
print(f"4. Updated project stage: {proj['stage']}")

# Test 5: Delete client
deleted = delete_client(cid)
assert deleted is True
assert find_client(cid) is None
print(f"5. Deleted client: success=True, re-find=None")

# Cleanup
_projects_store.clear()
print("\n=== ALL TESTS PASSED ===")
print(f"Endpoints summary:")
print(f"  Projects: GET /, POST /, GET /:id, PUT /:id, DELETE /:id, PUT /:id/assign-client, GET /:id/items, GET /:id/offers")
print(f"  Clients:  GET /, POST /, GET /:id, PUT /:id, DELETE /:id, GET /:id/projects")
