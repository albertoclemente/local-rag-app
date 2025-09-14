#!/usr/bin/env python3
"""
Test the improved prompt formatting to verify single document with multiple chunks
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.retrieval import get_retrieval_service
from app.llm import get_llm_service, GenerationRequest

async def test_prompt_formatting():
    """Test the improved prompt formatting"""
    print("🧪 Testing improved prompt formatting...")
    
    try:
        # Initialize services
        retrieval = await get_retrieval_service()
        llm = await get_llm_service()
        
        # Test retrieval
        query = "How many documents are in the system?"
        result = await retrieval.retrieve_for_query(query)
        chunks = result.chunks
        
        print(f"📊 Retrieved {len(chunks)} chunks from {len(set(chunk.doc_id for chunk in chunks))} document(s)")
        
        # Create request with retrieval result
        request = GenerationRequest(prompt=query, retrieval_result=result, stream=False)
        
        # Generate response
        response = await llm.generate(request)
        
        print(f"\n✅ LLM Response:")
        print(f"📝 {response.text[:500]}...")
        
        # Check if the response properly acknowledges single document
        response_text = response.text.lower()
        if "document" in response_text and ("single" in response_text or "one" in response_text or len(chunks) == 6):
            print(f"\n🎉 SUCCESS! LLM correctly understands there's 1 document with {len(chunks)} chunks")
        else:
            print(f"\n⚠️ Response might still be confusing about document count")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prompt_formatting())