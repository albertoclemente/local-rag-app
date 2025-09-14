#!/usr/bin/env python3
"""
Final RAG functionality test to verify LLM can access documents
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.storage import get_document_storage_service
from app.retrieval import get_retrieval_service
from app.llm import get_llm_service

async def test_rag_functionality():
    """Test the complete RAG pipeline"""
    print("🧪 Testing RAG functionality...")
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        storage = await get_document_storage_service()
        retrieval = await get_retrieval_service()
        llm = await get_llm_service()
        print("✅ Services initialized")
        
        # Check documents
        print("\n📄 Checking documents...")
        documents = await storage.list_documents()
        print(f"Found {len(documents)} documents:")
        for doc in documents:
            print(f"  - {doc.name} (ID: {doc.id[:8]}..., chunks: {doc.chunk_count})")
        
        if not documents:
            print("❌ No documents found!")
            return
        
        if all(doc.chunk_count == 0 for doc in documents):
            print("❌ All documents have 0 chunks!")
            return
        
        # Test retrieval
        print("\n🔍 Testing retrieval...")
        query = "What are the main lessons learned from building with LLMs?"
        
        try:
            result = await retrieval.retrieve_for_query(query)
            results = result.chunks
            print(f"✅ Retrieved {len(results)} chunks")
            
            if results:
                print("📝 Sample result:")
                print(f"   Score: {results[0].score:.3f}")
                print(f"   Text preview: {results[0].text[:100]}...")
            else:
                print("❌ No results returned from retrieval")
                return
                
        except Exception as e:
            print(f"❌ Retrieval failed: {e}")
            return
        
        # Test LLM with context
        print("\n🤖 Testing LLM with retrieved context...")
        context = "\n\n".join([result.text for result in results[:3]])
        
        prompt = f"""Based on the following context from the documents, answer this question: {query}

Context:
{context}

Answer:"""
        
        try:
            from backend.app.llm import GenerationRequest
            request = GenerationRequest(prompt=prompt, stream=False)
            
            response = await llm.generate(request)
            response_text = response.text
            print("✅ LLM response generated successfully")
            print(f"📝 Response preview: {response_text[:200]}...")
            
            # Check if the response contains relevant information
            if len(response_text) > 50 and "LLM" in response_text:
                print("🎉 SUCCESS! RAG system is working correctly")
                print(f"   Documents: {len(documents)} (with {sum(d.chunk_count for d in documents)} total chunks)")
                print(f"   Retrieval: {len(results)} relevant chunks found")
                print(f"   LLM: Generated {len(response_text)} character response")
                return True
            else:
                print("⚠️ LLM response seems incomplete or irrelevant")
                return False
                
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_functionality())
    exit(0 if success else 1)