#!/usr/bin/env python3
"""
Debug document indexing to find why chunkCount is 0
"""

import asyncio
import sys
import os
sys.path.append('/Users/alberto/projects/RAG_APP/backend')

async def debug_indexing():
    """Debug the document indexing process"""
    try:
        print("🔍 Starting indexing debug...")
        
        # Import services
        from app.storage import get_document_storage_service
        from app.parsing import get_document_parser_service
        from app.chunking import get_chunking_service
        from app.embeddings import embed_chunks
        from app.qdrant_index import get_qdrant_service
        from app.models import DocumentType
        
        # Get services
        storage = await get_document_storage_service()
        parser = await get_document_parser_service()
        chunker = await get_chunking_service()
        qdrant = await get_qdrant_service()
        
        print("✅ All services loaded")
        
        # Get documents
        docs = await storage.list_documents()
        print(f"📄 Found {len(docs)} documents")
        
        if not docs:
            print("❌ No documents found!")
            return
        
        # Take the first document
        doc = docs[0]
        print(f"🔧 Processing document: {doc.name} (ID: {doc.id})")
        print(f"   Status: {doc.status}")
        print(f"   Embedding status: {doc.embedding_status}")
        print(f"   Chunk count: {doc.chunk_count}")
        
        # Get the raw file path
        raw_path = await storage.get_raw_file_path(doc.id)
        if not raw_path:
            print(f"❌ No raw file found for {doc.id}")
            return
            
        print(f"📁 Raw file: {raw_path}")
        
        # Parse the document
        print("🔄 Parsing document...")
        try:
            parsed_data = await parser.parse_document(raw_path, doc.type)
            print(f"✅ Parsing successful")
            print(f"   Full text length: {len(parsed_data.get('full_text', ''))}")
            print(f"   Document type: {parsed_data.get('document_type', 'unknown')}")
            
            # Store parsed content
            await storage.store_parsed_content(doc.id, parsed_data)
            print("✅ Parsed content stored")
            
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Chunk the document
        print("✂️  Chunking document...")
        try:
            doc_type_str = parsed_data.get('document_type', 'pdf')
            doc_type = DocumentType(doc_type_str)
            
            chunked_doc = await chunker.chunk_document(
                doc.id,
                parsed_data.get('full_text', ''),
                parsed_data.get('structure', {}),
                doc_type
            )
            
            print(f"✅ Chunking successful")
            print(f"   Number of chunks: {len(chunked_doc.chunks)}")
            print(f"   Chunking strategy: {chunked_doc.chunking_params.strategy}")
            print(f"   Max chunk size: {chunked_doc.chunking_params.max_chunk_size}")
            print(f"   Chunking params: {chunked_doc.chunking_params.__dict__}")
            
            if len(chunked_doc.chunks) > 0:
                print(f"   First chunk preview: {chunked_doc.chunks[0][:100]}...")
            
            # Store chunking results
            chunk_data = {
                "chunks": chunked_doc.chunks,
                "metadata": [meta.__dict__ for meta in chunked_doc.metadata],
                "params": chunked_doc.chunking_params.__dict__,
                "rationale": chunked_doc.rationale,
                "stats": chunked_doc.stats
            }
            
            parsed_data["chunking"] = chunk_data
            await storage.store_parsed_content(doc.id, parsed_data)
            print("✅ Chunking results stored")
            
        except Exception as e:
            print(f"❌ Chunking failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Create embeddings
        print("🧠 Creating embeddings...")
        try:
            if len(chunked_doc.chunks) == 0:
                print("❌ No chunks to embed!")
                return
                
            chunk_dicts = [{"text": chunk} for chunk in chunked_doc.chunks]
            embedded_chunks = await embed_chunks(chunk_dicts)
            
            print(f"✅ Embeddings created for {len(embedded_chunks)} chunks")
            
            # Index in vector database
            print("🗃️  Indexing in vector database...")
            result = await qdrant.index_chunks(embedded_chunks, doc.id)
            print(f"✅ Vector indexing successful: {result}")
            
            # Update document status with chunk count (like the fixed API)
            await storage.update_document_metadata(doc.id, {
                "status": "indexed",
                "chunk_count": len(chunked_doc.chunks)
            })
            print(f"✅ Document status updated with chunk count: {len(chunked_doc.chunks)}")
            
        except Exception as e:
            print(f"❌ Embedding/indexing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Final verification
        print("\n🔍 Final verification...")
        updated_docs = await storage.list_documents()
        updated_doc = next((d for d in updated_docs if d.id == doc.id), None)
        
        if updated_doc:
            print(f"📊 Final status:")
            print(f"   Status: {updated_doc.status}")
            print(f"   Embedding status: {updated_doc.embedding_status}")
            print(f"   Chunk count: {updated_doc.chunk_count}")
            
            if updated_doc.chunk_count > 0:
                print("🎉 SUCCESS! Document is now properly indexed")
            else:
                print("❌ Still no chunks - there's a deeper issue")
        else:
            print("❌ Could not find updated document")
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_indexing())