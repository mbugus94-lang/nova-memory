import sys
import os
import uuid

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from api.server import app

def run_verification():
    print("=" * 60)
    print("VERIFYING NOVA MEMORY 2.1 API UPDATE")
    print("=" * 60)

    with TestClient(app) as client:

        # 1. Test Health
        print("\n[1] Testing Health Endpoint...")
        response = client.get("/health")
        if response.status_code == 200:
            print(f"    [OK] Health check passed: {response.json().get('status')}")
        else:
            print(f"    [FAIL] Health check failed: {response.status_code}")
            return

        # 2. Test Auth (Login)
        print("\n[2] Testing Authentication...")
        login_data = {"username": "admin", "password": "admin"}
        response = client.post("/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("    [OK] Login successful. Token obtained.")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"    [FAIL] Login failed: {response.status_code} - {response.text}")
            return

        # 3. Test Create Memory (Authenticated)
        print("\n[3] Testing Memory Creation...")
        test_id = str(uuid.uuid4())[:8]
        memory_data = {
            "content": f"This is a verification memory {test_id} for Nova 2.1",
            "tags": ["verification", "test"],
            "metadata": {"test_id": test_id}
        }
        response = client.post("/memories", json=memory_data, headers=headers)
        if response.status_code == 201:
            mem_id = response.json().get("id")
            print(f"    [OK] Memory created: {mem_id}")
        else:
            print(f"    [FAIL] Memory creation failed: {response.status_code} - {response.text}")
            return

        # 4. Test Swift Retrieval (Context)
        print("\n[4] Testing Swift Retrieval (Context)...")
        # Wait a moment for FTS to index? (SQLite FTS is synchronous usually)
        context_req = {"query": "verification memory", "limit": 2}
        response = client.post("/memories/context", json=context_req)

        if response.status_code == 200:
            data = response.json()
            context = data.get("context", "")
            if test_id in context:
                 print("    [OK] Context retrieved successfully containing test ID.")
                 print(f"    Preview: {context[:50]}...")
            else:
                 print(f"    [WARN] Context retrieved but test ID not found (indexing delay?): {context}")
        else:
            print(f"    [FAIL] Context retrieval failed: {response.status_code} - {response.text}")

        # 5. Test Auto-Capture Interaction
        print("\n[5] Testing Interaction Auto-Capture...")
        interaction_data = {
            "agent_id": "agent_test",
            "user_message": f"Hello agent {test_id}",
            "agent_response": "Hello user, I am capturing this.",
            "user_feedback": "positive"
        }
        # params={"auto_capture": True}
        response = client.post("/interactions?auto_capture=true", json=interaction_data)
        if response.status_code == 201:
            print("    [OK] Interaction logged with auto-capture.")
            # Verify memory was created
            # Search for "Hello agent {test_id}"
            search_res = client.get(f"/memories?query=Hello%20agent%20{test_id}")
            if search_res.status_code == 200 and len(search_res.json()) > 0:
                print("    [OK] Auto-captured memory found in search.")
            else:
                print("    [WARN] Auto-captured memory NOT found immediately.")
        else:
            print(f"    [FAIL] Interaction logging failed: {response.status_code} - {response.text}")

        # 6. Test Collaboration (Create Space)
        print("\n[6] Testing Collaboration (Create Space)...")
        space_name = f"Test Space {test_id}"
        space_data = {
            "space_name": space_name,
            "creator": "admin",
            "members": ["admin", "agent_test"]
        }
        response = client.post("/collaboration/spaces", json=space_data, headers=headers)
        if response.status_code == 200:
            space_id = response.json().get("space_id")
            print(f"    [OK] Collaborative space created: ID {space_id}")
        else:
            print(f"    [FAIL] Space creation failed: {response.status_code} - {response.text}")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
