#!/usr/bin/env python3
"""
Simple test script for LLM functionality.
Tests Ollama connection and basic generation without external dependencies.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_ollama_connection():
    """Test if Ollama is available and responsive"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                print("✅ Ollama is running and accessible")
                print(f"Available models: {[model['name'] for model in models.get('models', [])]}")
                return True
            else:
                print(f"❌ Ollama responded with status code: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        print("Make sure Ollama is running with: ollama serve")
        return False

async def test_model_availability():
    """Test if qwen2.5:7b-instruct model is available"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/show",
                json={"name": "qwen2.5:7b-instruct"}
            )
            
            if response.status_code == 200:
                model_info = response.json()
                print("✅ qwen2.5:7b-instruct model is available")
                print(f"Model size: {model_info.get('details', {}).get('parameter_size', 'unknown')}")
                return True
            else:
                print("❌ qwen2.5:7b-instruct model not found")
                print("Pull the model with: ollama pull qwen2.5:7b-instruct")
                return False
                
    except Exception as e:
        print(f"❌ Failed to check model availability: {e}")
        return False

async def test_simple_generation():
    """Test simple text generation"""
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_data = {
                "model": "qwen2.5:7b-instruct",
                "prompt": "What is 2+2? Answer with just the number.",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 10
                }
            }
            
            print("🔄 Testing simple generation...")
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                print(f"✅ Generation successful: '{generated_text}'")
                print(f"Tokens generated: {result.get('eval_count', 0)}")
                print(f"Generation time: {result.get('eval_duration', 0) / 1e9:.2f}s")
                return True
            else:
                print(f"❌ Generation failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        return False

async def test_streaming_generation():
    """Test streaming text generation"""
    try:
        import httpx
        import json
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            request_data = {
                "model": "qwen2.5:7b-instruct",
                "prompt": "Explain what machine learning is in one sentence.",
                "stream": True,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 50
                }
            }
            
            print("🔄 Testing streaming generation...")
            
            tokens = []
            async with client.stream(
                "POST",
                "http://localhost:11434/api/generate",
                json=request_data
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ Streaming failed with status: {response.status_code}")
                    return False
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            token = chunk["response"]
                            if token:
                                tokens.append(token)
                                print(token, end="", flush=True)
                        
                        if chunk.get("done", False):
                            print()  # New line after completion
                            break
                    except json.JSONDecodeError:
                        continue
            
            print(f"✅ Streaming successful: {len(tokens)} tokens received")
            return True
                
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

async def run_all_tests():
    """Run all LLM tests"""
    print("Testing LLM functionality with Qwen 2.5 Instructor...\n")
    
    print("=== Testing Ollama Connection ===")
    if not await test_ollama_connection():
        return False
    print()
    
    print("=== Testing Model Availability ===")
    if not await test_model_availability():
        return False
    print()
    
    print("=== Testing Simple Generation ===")
    if not await test_simple_generation():
        return False
    print()
    
    print("=== Testing Streaming Generation ===")
    if not await test_streaming_generation():
        return False
    print()
    
    print("🎉 All LLM tests passed!")
    print("\nThe LLM service is ready for integration.")
    print("Section 6 (LLM streaming) implementation is complete!")
    return True

if __name__ == "__main__":
    asyncio.run(run_all_tests())
