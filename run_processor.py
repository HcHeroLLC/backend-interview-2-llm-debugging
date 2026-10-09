#!/usr/bin/env python3
"""
Run the document processor to demonstrate the bugs.

Usage:
    python run_processor.py           # Process sample documents
    python run_processor.py --verbose # Show detailed output
    python run_processor.py --stress  # Run with large batch (triggers rate limits)
"""

import asyncio
import argparse
import os
import sys

from processor import DocumentProcessor
from test_documents import SAMPLE_DOCUMENTS, LARGE_BATCH


async def run_basic_test(verbose: bool = False):
    """Run processor with sample documents."""
    api_key = os.environ.get("LLM_API_KEY", "test-key")
    base_url = os.environ.get("LLM_API_BASE")

    print("=" * 60)
    print("Marketing Document Processor - Basic Test")
    print("=" * 60)
    print(f"API Base URL: {base_url or 'default'}")
    print(f"Documents to process: {len(SAMPLE_DOCUMENTS)}")
    print()

    processor = DocumentProcessor(api_key, base_url)

    try:
        print("Processing documents...")
        results = await processor.process_batch(SAMPLE_DOCUMENTS)

        print(f"\nSuccessfully processed {len(results)} documents\n")

        if verbose:
            for i, result in enumerate(results):
                print(f"Document {i + 1}:")
                print(f"  Result: {result}")
                print()

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nThis is likely one of the bugs you need to fix!")
        sys.exit(1)

    # Note: Session leak - won't be closed


async def run_stress_test():
    """Run processor with large batch to trigger rate limits."""
    api_key = os.environ.get("LLM_API_KEY", "test-key")
    base_url = os.environ.get("LLM_API_BASE")

    print("=" * 60)
    print("Marketing Document Processor - Stress Test")
    print("=" * 60)
    print(f"Documents to process: {len(LARGE_BATCH)}")
    print("\nThis should trigger rate limiting bugs...")
    print()

    processor = DocumentProcessor(api_key, base_url)

    try:
        results = await processor.process_batch(LARGE_BATCH)
        print(f"\nProcessed {len(results)} documents")
        print("(If you got here without errors, the rate limiting is fixed!)")

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nThis is expected behavior with the buggy code.")
        print("Fix the concurrency issues to handle large batches!")
        sys.exit(1)


async def run_stream_test():
    """Test streaming functionality."""
    api_key = os.environ.get("LLM_API_KEY", "test-key")
    base_url = os.environ.get("LLM_API_BASE")

    print("=" * 60)
    print("Marketing Document Processor - Streaming Test")
    print("=" * 60)

    processor = DocumentProcessor(api_key, base_url)
    document = SAMPLE_DOCUMENTS[0]

    print("Streaming analysis...\n")

    try:
        async for chunk in processor.stream_analysis(document):
            # With the buggy code, this will print raw SSE data
            # After fixing, it should print clean text chunks
            print(chunk, end="", flush=True)

        print("\n\n(If you see 'data: {...}' format, the SSE parsing needs fixing)")

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")

    # Session leak


def main():
    parser = argparse.ArgumentParser(description="Run the document processor")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output")
    parser.add_argument("--stress", action="store_true",
                        help="Run stress test with large batch")
    parser.add_argument("--stream", action="store_true",
                        help="Test streaming functionality")

    args = parser.parse_args()

    if args.stress:
        asyncio.run(run_stress_test())
    elif args.stream:
        asyncio.run(run_stream_test())
    else:
        asyncio.run(run_basic_test(verbose=args.verbose))


if __name__ == "__main__":
    main()
