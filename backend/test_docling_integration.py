"""
Test script for Docling integration.
Run this to verify that Docling conversion is working.
"""

import asyncio
from pathlib import Path
import sys

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.markdown_converter import get_markdown_converter
from app.parsing import get_document_parser
from app.models import DocumentType


async def test_markdown_converter():
    """Test the markdown converter directly"""
    print("\n" + "="*60)
    print("Testing Markdown Converter")
    print("="*60)
    
    converter = get_markdown_converter()
    
    # Check if Docling is available
    if not converter.is_available():
        print("❌ Docling is NOT available")
        print("   Please check installation: pip install docling")
        return False
    
    print("✅ Docling is available and initialized")
    
    # Show supported formats
    supported = converter.get_supported_formats()
    print(f"\n📄 Supported formats ({len(supported)}):")
    print(f"   {', '.join(supported)}")
    
    return True


async def test_document_parser():
    """Test the document parser with Docling integration"""
    print("\n" + "="*60)
    print("Testing Document Parser Integration")
    print("="*60)
    
    parser = get_document_parser()
    
    # Check supported types
    supported_types = parser.get_supported_types()
    print(f"\n📚 Supported document types ({len(supported_types)}):")
    print(f"   {', '.join(supported_types)}")
    
    # Check file type detection for new formats
    test_files = {
        'test.html': DocumentType.HTML,
        'test.pptx': DocumentType.PPTX,
        'test.pdf': DocumentType.PDF,
        'test.docx': DocumentType.DOCX,
    }
    
    print("\n🔍 File type detection:")
    for filename, expected_type in test_files.items():
        detected = parser.detect_file_type(Path(filename))
        status = "✅" if detected == expected_type else "❌"
        print(f"   {status} {filename} → {detected}")
    
    return True


async def test_with_sample_file():
    """Test conversion with a sample file if available"""
    print("\n" + "="*60)
    print("Testing with Sample Files")
    print("="*60)
    
    # Check for sample PDF in the project
    sample_files = [
        Path("/Users/alberto/projects/RAG_APP/sole_08011402CLMLRT78S03H926F000005.pdf"),
        Path("/Users/alberto/RAGApp/library/raw/57a90289-e362-4157-870c-4d66bc1aa974/57a90289-e362-4157-870c-4d66bc1aa974.pdf"),
    ]
    
    converter = get_markdown_converter()
    
    for sample_file in sample_files:
        if sample_file.exists():
            print(f"\n📄 Testing with: {sample_file.name}")
            try:
                result = await converter.convert_to_markdown(sample_file)
                print(f"   ✅ Conversion successful!")
                print(f"   📊 Stats:")
                print(f"      - Pages: {result.get('page_count', 'N/A')}")
                print(f"      - Characters: {result['char_count']:,}")
                print(f"      - Words: {result['word_count']:,}")
                print(f"      - Headings: {result['structure'].get('heading_count', 0)}")
                print(f"      - Tables: {result['structure'].get('table_count', 0)}")
                print(f"\n   �� First 500 characters of Markdown:")
                print(f"   {'-'*56}")
                print(f"   {result['markdown'][:500]}...")
                return True
            except Exception as e:
                print(f"   ❌ Conversion failed: {e}")
                return False
    
    print("   ⚠️  No sample files found for testing")
    print("   💡 Upload a document to test conversion")
    return None


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 DOCLING INTEGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Markdown Converter
    results.append(await test_markdown_converter())
    
    # Test 2: Document Parser
    results.append(await test_document_parser())
    
    # Test 3: Sample file conversion
    sample_result = await test_with_sample_file()
    if sample_result is not None:
        results.append(sample_result)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("\n🎉 Docling integration is working correctly!")
        print("📥 Upload documents to your RAG app - they will be automatically")
        print("   converted to Markdown for better retrieval quality.")
    else:
        print(f"⚠️  Some tests failed ({passed}/{total} passed)")
        print("\n🔧 Please check the errors above and ensure:")
        print("   1. Docling is installed: pip install docling")
        print("   2. All dependencies are available")
        print("   3. Sample files exist for testing")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
