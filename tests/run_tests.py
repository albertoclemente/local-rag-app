#!/usr/bin/env python3
"""
Test runner for RAG WebApp
Runs tests in isolated environment without backend import conflicts
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment to prevent backend auto-initialization
os.environ['RAG_TEST_MODE'] = '1'

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run RAG WebApp tests')
    parser.add_argument('test_name', nargs='?', help='Specific test to run (e.g., tc_func_010)')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    if args.test_name == 'tc_func_010':
        from simple_test_010 import main
        main()
    elif args.test_name == 'tc_func_011':
        from test_tc_func_011 import run_reindex_test
        run_reindex_test()
    elif args.test_name == 'tc_func_020':
        from test_tc_func_020 import run_tc_func_020
        run_tc_func_020()
    elif args.all:
        print("Running all tests...")
        # Run TC-FUNC-010
        print("\n" + "="*50)
        print("Running TC-FUNC-010: Adaptive Chunking")
        print("="*50)
        from simple_test_010 import main
        main()
        
        # Run TC-FUNC-011
        print("\n" + "="*50)
        print("Running TC-FUNC-011: Re-index on param change")
        print("="*50)
        from test_tc_func_011 import run_reindex_test
        run_reindex_test()
    else:
        print("Available tests:")
        print("  tc_func_010  - Adaptive chunking test")
        print("  tc_func_011  - Re-index on param change test")
        print("Usage: python run_tests.py tc_func_011")
