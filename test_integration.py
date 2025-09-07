#!/usr/bin/env python3
"""
Simple test to verify the vector indexing integration works correctly.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'convert_pdf', 'src'))

try:
    from pdf2md import build_workflow, ConversionState
    print("✓ Successfully imported pdf2md module")
    
    # Test building the workflow
    workflow = build_workflow()
    print("✓ Successfully built workflow with vector indexing node")
    
    # Test that the workflow has the expected nodes
    expected_nodes = ["check_pdf_type", "extract_text", "process_to_markdown", "save_markdown", "vector_indexing"]
    
    # Get the workflow graph nodes (this is implementation specific)
    workflow_nodes = list(workflow.graph.nodes.keys())
    print(f"✓ Workflow nodes: {workflow_nodes}")
    
    for node in expected_nodes:
        if node in workflow_nodes:
            print(f"✓ Node '{node}' found in workflow")
        else:
            print(f"✗ Node '{node}' missing from workflow")
            sys.exit(1)
    
    print("\n✓ All integration tests passed!")
    print("✓ Vector indexing has been successfully integrated into the LangGraph workflow")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)