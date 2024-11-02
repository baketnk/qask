import aiohttp
import json
import random
import asyncio
from typing import AsyncGenerator, Dict
from datetime import datetime
import base64
import logging

async def generate_headers(api_key: str, api_type: str = "openai") -> Dict[str, str]:
    """Generate headers based on API type."""
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_type == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
    elif api_type == "openrouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "https://github.com/yourusername/yourproject"  # Required for OR
        headers["X-Title"] = "Your Application Name"  # OpenRouter stats
    else:  # openai
        headers["Authorization"] = f"Bearer {api_key}"
    
    return headers

async def llm_stream(
    messages: list,
    api_base: str,
    api_key: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    api_type: str = "openai",
    add_noise: bool = True,
    stream: bool = True
) -> AsyncGenerator:
    """
    Stream responses from various LLM providers with OpenAI-like output format.
    
    Args:
        messages: List of message dictionaries
        api_key: API key for the service
        model: Model identifier
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        api_base: Base URL for API
        api_type: One of "openai", "anthropic", "openrouter"
        add_noise: Whether to add natural streaming noise
        stream: Whether to stream the response
    """
    headers = await generate_headers(api_key, api_type)
    
    # Prepare the request payload based on API type
    if api_type == "anthropic":
        system_prompt = "" 
        if messages[0]["role"] == "system":
            system_prompt = messages[0]["content"]
            messages = messages[1:]
        payload = {
            "model": model,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "system": system_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        endpoint = f"{api_base}/v1/messages"
    else:  # openai-like
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        endpoint = f"{api_base}/chat/completions"

    async with aiohttp.ClientSession() as session:
        logging.info(f"llm_stream to {endpoint} {model}")
        async with session.post(endpoint, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API request failed with status {response.status}: {error_text}")

            # Handle streaming response
            if stream:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        line = line[6:]  # Remove 'data: ' prefix
                    if line:
                        try:
                            if line == '[DONE]':
                                break
                                
                            data = json.loads(line)
                            
                            # Handle different API response formats
                            if api_type == "anthropic":
                                delta = data.get('delta', {}).get('text', '')
                            else:  # openai-like
                                delta = data.get('choices', [{}])[0].get('delta', {}).get('content', '')

                            if delta:
                                if add_noise:
                                    yield {
                                        "choices": [{
                                            "delta": {"content": delta},
                                            "noise": str(base64.b64encode(random.randbytes(16))),
                                            "finish_reason": None
                                        }],
                                        "created": int(datetime.now().timestamp())
                                    }
                                    await asyncio.sleep(random.uniform(0.01, 0.1))
                                else:
                                    yield {
                                        "choices": [{
                                            "delta": {"content": delta},
                                            "finish_reason": None
                                        }],
                                        "created": int(datetime.now().timestamp())
                                    }
                                    
                        except json.JSONDecodeError:
                            continue
                
                # Send final message
                yield {
                    "choices": [{
                        "delta": {},
                        "finish_reason": "stop"
                    }],
                    "created": int(datetime.now().timestamp())
                }
            else:
                # Handle non-streaming response
                response_json = await response.json()
                yield response_json
