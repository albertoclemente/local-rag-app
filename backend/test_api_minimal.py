"""
Minimal test version of app.api to isolate the issue
"""

from fastapi import APIRouter

# Test 1: Just create a router
print("Creating router...")
router = APIRouter()
print(f"Router created: {router}")

# Test 2: Try to add a simple route
@router.get("/test")
async def test_endpoint():
    return {"message": "test"}

print("Route added successfully")
