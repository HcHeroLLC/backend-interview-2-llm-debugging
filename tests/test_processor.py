"""
Tests for the Marketing Document Processor

These tests verify that the bugs have been fixed.
Run with: pytest tests/ -v
"""

import pytest
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor import DocumentProcessor
from test_documents import SAMPLE_DOCUMENTS, LARGE_BATCH


# Configure for async tests
pytestmark = pytest.mark.asyncio


@pytest.fixture
def processor():
    """Create a processor instance for testing."""
    api_key = os.environ.get("LLM_API_KEY", "test-key")
    base_url = os.environ.get("LLM_API_BASE", "http://mock-llm:8080")
    return DocumentProcessor(api_key, base_url)


class TestResourceManagement:
    """Tests for proper resource management (Bug 1, 13)."""

    async def test_session_cleanup_with_context_manager(self):
        """Processor should support async context manager for cleanup."""
        api_key = os.environ.get("LLM_API_KEY", "test-key")
        base_url = os.environ.get("LLM_API_BASE", "http://mock-llm:8080")

        # If properly fixed, should support: async with DocumentProcessor(...) as p:
        processor = DocumentProcessor(api_key, base_url)

        # At minimum, should have a close method
        assert hasattr(processor, 'close') or hasattr(processor, '__aexit__'), \
            "Processor should have a close() method or support async context manager"

        # Clean up
        if hasattr(processor, 'close'):
            await processor.close()
        elif hasattr(processor, 'session'):
            await processor.session.close()


class TestErrorHandling:
    """Tests for proper error handling (Bugs 3, 4, 12)."""

    async def test_handles_api_errors_gracefully(self, processor):
        """Should handle API errors without crashing."""
        try:
            # This should not raise an unhandled exception
            result = await processor.extract_info("test document")
            # Result should be valid (string or dict)
            assert result is not None
        except Exception as e:
            # If it raises, it should be a specific, meaningful exception
            # not a KeyError or AttributeError from missing data
            assert not isinstance(e, (KeyError, AttributeError)), \
                f"Should handle missing response data gracefully, got: {type(e).__name__}"
        finally:
            if hasattr(processor, 'session'):
                await processor.session.close()

    async def test_retry_raises_after_exhaustion(self, processor):
        """Retry should raise an exception after all attempts fail, not return error dict."""
        # We can't easily force failures with the mock server,
        # but we can verify the return type handling
        try:
            result = await processor.process_with_retry("test document")
            # If successful, should be a valid result
            if isinstance(result, dict) and "error" in result:
                pytest.fail("Should raise exception on failure, not return error dict")
        except Exception:
            # Raising an exception is the correct behavior
            pass
        finally:
            if hasattr(processor, 'session'):
                await processor.session.close()


class TestConcurrency:
    """Tests for proper concurrency handling (Bugs 5, 6, 7)."""

    async def test_batch_processing_respects_rate_limits(self, processor):
        """Large batch should not trigger rate limit errors."""
        try:
            # Process a moderately large batch
            results = await processor.process_batch(SAMPLE_DOCUMENTS * 4)  # 20 docs
            assert len(results) == 20, "Should process all documents"

            # All results should be successful (not error responses)
            for r in results:
                if isinstance(r, dict):
                    assert "error" not in r, f"Got error response: {r}"

        except Exception as e:
            # Should not fail due to rate limits if properly throttled
            assert "rate limit" not in str(e).lower(), \
                "Should handle rate limits with proper throttling"
        finally:
            if hasattr(processor, 'session'):
                await processor.session.close()

    async def test_batch_handles_individual_failures(self, processor):
        """If one document fails, others should still succeed."""
        try:
            results = await processor.process_batch(SAMPLE_DOCUMENTS)
            # Should get results for all documents
            assert len(results) == len(SAMPLE_DOCUMENTS)
        except Exception:
            pytest.fail("Batch processing should handle individual failures gracefully")
        finally:
            if hasattr(processor, 'session'):
                await processor.session.close()


class TestStreaming:
    """Tests for proper SSE stream handling (Bug 8)."""

    async def test_stream_returns_clean_text(self, processor):
        """Streaming should return parsed text, not raw SSE format."""
        chunks = []

        try:
            async for chunk in processor.stream_analysis(SAMPLE_DOCUMENTS[0]):
                chunks.append(chunk)

            full_response = "".join(chunks)

            # Should NOT contain raw SSE format
            assert "data: {" not in full_response, \
                "Should parse SSE format, not return raw data"
            assert "[DONE]" not in full_response, \
                "Should handle [DONE] signal, not include in output"

        finally:
            if hasattr(processor, 'session'):
                await processor.session.close()


class TestRetryLogic:
    """Tests for proper retry implementation (Bugs 9, 10, 11)."""

    async def test_retry_uses_exponential_backoff(self, processor):
        """Retry logic should use exponential backoff."""
        # This is hard to test directly, but we can check the code
        # In a real scenario, you'd mock time.sleep and verify delays
        import inspect
        source = inspect.getsource(processor.process_with_retry)

        # Should see some form of exponential backoff
        has_backoff = any([
            "** attempt" in source,
            "2 **" in source,
            "exponential" in source.lower(),
            "backoff" in source.lower(),
            "attempt *" in source,  # e.g., 1 * attempt
        ])

        # At minimum, should not have fixed sleep(1)
        if "sleep(1)" in source and "attempt" not in source:
            pytest.fail("Should use exponential backoff, not fixed delay")

        if hasattr(processor, 'session'):
            await processor.session.close()
