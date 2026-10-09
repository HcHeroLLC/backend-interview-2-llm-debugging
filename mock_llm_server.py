"""
Mock LLM Server - Simulates OpenAI's Chat Completions API

This server is used for the technical interview exercise.
It simulates realistic API behavior including:
- Normal responses
- Rate limiting (after too many concurrent requests)
- Streaming responses (SSE format)
- Occasional errors

Candidates should NOT modify this file.
"""

from aiohttp import web
import json
import asyncio
import random
from datetime import datetime

# Track concurrent requests for rate limiting simulation
active_requests = 0
total_requests = 0
MAX_CONCURRENT = 5  # Simulate rate limiting


async def health_check(request):
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "service": "mock-llm-server",
        "timestamp": datetime.utcnow().isoformat()
    })


async def chat_completions(request):
    """
    Mock OpenAI chat completions endpoint.

    Supports both regular and streaming responses.
    Simulates rate limiting when too many concurrent requests.
    """
    global active_requests, total_requests

    active_requests += 1
    total_requests += 1
    request_id = total_requests

    try:
        # Simulate rate limiting
        if active_requests > MAX_CONCURRENT:
            await asyncio.sleep(0.1)  # Small delay before error
            return web.json_response(
                {
                    "error": {
                        "message": "Rate limit exceeded. Please retry after some time.",
                        "type": "rate_limit_error",
                        "code": "rate_limit_exceeded"
                    }
                },
                status=429,
                headers={"Retry-After": "1"}
            )

        # Parse request
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": {"message": "Invalid JSON", "type": "invalid_request_error"}},
                status=400
            )

        # Validate request
        if "messages" not in data:
            return web.json_response(
                {"error": {"message": "messages is required", "type": "invalid_request_error"}},
                status=400
            )

        # Simulate processing time
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Occasionally simulate a server error (5% chance)
        if random.random() < 0.05:
            return web.json_response(
                {"error": {"message": "Internal server error", "type": "server_error"}},
                status=500
            )

        # Get the user message to generate contextual response
        user_message = ""
        for msg in data.get("messages", []):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")

        # Check if streaming is requested
        if data.get("stream", False):
            return await stream_response(request, user_message)

        # Generate mock extraction response
        extracted_data = generate_mock_extraction(user_message)

        return web.json_response({
            "id": f"chatcmpl-mock-{request_id}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": data.get("model", "gpt-4"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(extracted_data)
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": 50,
                "total_tokens": len(user_message.split()) + 50
            }
        })

    finally:
        active_requests -= 1


async def stream_response(request, user_message: str):
    """
    Stream a response using Server-Sent Events (SSE) format.

    This is the correct SSE format that OpenAI uses:
    - Each chunk is prefixed with "data: "
    - Chunks are separated by double newlines
    - Stream ends with "data: [DONE]"
    """
    response = web.StreamResponse(
        status=200,
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
    await response.prepare(request)

    # Generate analysis text in chunks
    analysis_chunks = [
        "Based on ",
        "the document ",
        "provided, ",
        "I can see ",
        "this is ",
        "a marketing record ",
        "containing ",
        "campaign ",
        "information. ",
        "The key ",
        "details ",
        "extracted ",
        "are as ",
        "follows..."
    ]

    for i, chunk in enumerate(analysis_chunks):
        # Create SSE-formatted chunk
        chunk_data = {
            "id": f"chatcmpl-stream-{i}",
            "object": "chat.completion.chunk",
            "choices": [{
                "index": 0,
                "delta": {"content": chunk} if i > 0 else {"role": "assistant", "content": chunk},
                "finish_reason": None
            }]
        }

        # Write in SSE format
        sse_line = f"data: {json.dumps(chunk_data)}\n\n"
        await response.write(sse_line.encode('utf-8'))
        await asyncio.sleep(0.05)  # Simulate streaming delay

    # Send final chunk with finish_reason
    final_chunk = {
        "id": "chatcmpl-stream-final",
        "object": "chat.completion.chunk",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    await response.write(f"data: {json.dumps(final_chunk)}\n\n".encode('utf-8'))

    # Send done signal
    await response.write(b"data: [DONE]\n\n")

    return response


def generate_mock_extraction(document_text: str) -> dict:
    """Generate a mock extraction based on document content."""

    # Try to extract some realistic-looking data from the document
    # This simulates what an LLM would return

    # Default values
    result = {
        "campaign_name": "Unknown Campaign",
        "channel": "Unknown",
        "budget": None,
        "launch_date": None,
        "document_type": "unknown"
    }

    # Simple keyword matching for mock purposes
    text_lower = document_text.lower()

    if "campaign brief" in text_lower or "brief" in text_lower:
        result["document_type"] = "campaign_brief"
    elif "postmortem" in text_lower:
        result["document_type"] = "postmortem"
    elif "budget change" in text_lower:
        result["document_type"] = "budget_change"

    # Extract campaign name patterns (very simplified)
    if "product launch" in text_lower:
        result["campaign_name"] = "Spring Product Launch"
    elif "webinar" in text_lower:
        result["campaign_name"] = "Webinar Series"
    elif "retargeting" in text_lower:
        result["campaign_name"] = "Retargeting Push"
    elif "co-marketing" in text_lower:
        result["campaign_name"] = "Partner Co-Marketing"
    elif "seo" in text_lower:
        result["campaign_name"] = "SEO Content Refresh"

    # Extract channel
    for channel in ["email", "paid social", "content", "events", "search"]:
        if channel in text_lower:
            result["channel"] = channel.title()
            break

    # Extract budget (look for dollar amounts)
    import re
    budget_match = re.search(r'\$([\d,]+)', document_text)
    if budget_match:
        try:
            result["budget"] = int(budget_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Extract dates (simplified) - prefer a date near "launch"
    date_match = (
        re.search(r'launch\D{0,20}(\d{4}-\d{2}-\d{2})', document_text, re.IGNORECASE)
        or re.search(r'(\d{4}-\d{2}-\d{2})', document_text)
    )
    if date_match:
        result["launch_date"] = date_match.group(1)

    return result


# Create and configure the app
app = web.Application()
app.router.add_get('/health', health_check)
app.router.add_post('/v1/chat/completions', chat_completions)


if __name__ == '__main__':
    print("Starting Mock LLM Server on port 8080...")
    print(f"Max concurrent requests before rate limiting: {MAX_CONCURRENT}")
    web.run_app(app, host='0.0.0.0', port=8080)
