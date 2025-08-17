import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
import requests
import aiohttp
from ovos_utils.log import LOG

logger = LOG.create_logger(__name__)


class N8NClient:
    def __init__(self, config: Dict[str, Any]):
        self.webhook_url = config.get("webhook_url", "http://localhost:5678/webhook/chat")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.use_daily_session = config.get("use_daily_session", True)
        self.session_id_prefix = config.get("session_id_prefix", "jarvis")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._session = None
    
    def _get_session_id(self) -> str:
        """Generate daily session ID in format: prefix-YYYY-MM-DD"""
        if self.use_daily_session:
            today = datetime.now().strftime("%Y-%m-%d")
            return f"{self.session_id_prefix}-{today}"
        else:
            # Fallback to config session_id or generate timestamp-based one
            return self.session_id_prefix or f"session-{datetime.now().isoformat()}"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def send_query_sync(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        payload = {
            "message": query,
            "session_id": self._get_session_id()
        }
        
        if context:
            payload["context"] = context
        
        logger.debug(f"Sending to n8n webhook: {self.webhook_url}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        logger.debug(f"Request headers: {self.headers}")
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Log response details safely
            try:
                logger.debug(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response content-type: {response.headers.get('content-type', 'not set')}")
            except Exception as e:
                logger.error(f"Error logging response details: {e}")
            
            # Get raw response text
            try:
                response_text = response.text
                if response_text:
                    # Safely log first part of response
                    log_text = response_text if len(response_text) < 500 else response_text[:500] + "..."
                    logger.debug(f"N8N raw response text: {log_text}")
                else:
                    logger.warning("N8N returned empty response body")
                    return {"type": "error", "error": "Empty response from n8n"}
            except Exception as e:
                logger.error(f"Error getting response text: {e}")
                return {"type": "error", "error": f"Failed to read response: {e}"}
            
            # Try to parse as JSON
            try:
                result = response.json()
                logger.debug(f"Successfully parsed as JSON")
            except json.JSONDecodeError as e:
                # If not JSON, treat as plain text response
                logger.debug(f"Response is not valid JSON: {e}")
                logger.debug(f"Treating as plain text")
                result = response_text
            except Exception as e:
                logger.error(f"Unexpected error parsing response: {e}")
                result = response_text
            
            return self._parse_response(result)
            
        except requests.exceptions.Timeout:
            logger.error(f"N8N webhook timeout after {self.timeout} seconds")
            return {"type": "error", "error": "Request timeout"}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"N8N webhook not found (404): {self.webhook_url}")
                return {"type": "error", "error": f"404 - Webhook not found at {self.webhook_url}"}
            else:
                logger.error(f"N8N webhook HTTP error: {e}")
                return {"type": "error", "error": f"HTTP {e.response.status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"N8N webhook request failed: {e}")
            return {"type": "error", "error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse N8N response: {e}")
            return {"type": "error", "error": "Invalid JSON response from webhook"}
    
    async def send_query_async(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        payload = {
            "message": query,
            "session_id": self._get_session_id()
        }
        
        if context:
            payload["context"] = context
        
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.debug(f"N8N response: {result}")
                return self._parse_response(result)
                
        except asyncio.TimeoutError:
            logger.error(f"N8N webhook timeout after {self.timeout} seconds")
            return {"type": "error", "error": "Request timeout"}
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.error(f"N8N webhook not found (404): {self.webhook_url}")
                return {"type": "error", "error": f"404 - Webhook not found at {self.webhook_url}"}
            else:
                logger.error(f"N8N webhook HTTP error: {e}")
                return {"type": "error", "error": f"HTTP {e.status}: {str(e)}"}
        except aiohttp.ClientError as e:
            logger.error(f"N8N webhook request failed: {e}")
            return {"type": "error", "error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse N8N response: {e}")
            return {"type": "error", "error": "Invalid JSON response from webhook"}
    
    async def stream_query(self, query: str, context: Optional[Dict] = None) -> AsyncGenerator[Dict[str, Any], None]:
        payload = {
            "message": query,
            "session_id": self._get_session_id(),
            "stream": True
        }
        
        if context:
            payload["context"] = context
        
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=self.timeout * 2)
            
            async with session.post(
                self.webhook_url,
                json=payload,
                timeout=timeout
            ) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8').strip())
                            yield self._parse_response(data)
                        except json.JSONDecodeError:
                            continue
                            
        except asyncio.TimeoutError:
            logger.error(f"N8N webhook stream timeout")
            yield {"error": "Stream timeout", "type": "timeout"}
        except aiohttp.ClientError as e:
            logger.error(f"N8N webhook stream failed: {e}")
            yield {"error": str(e), "type": "request_error"}
    
    def _parse_response(self, response: Any) -> Dict[str, Any]:
        # Check for direct string response first
        if isinstance(response, str):
            logger.debug(f"Response is a string: {response}")
            return {
                "type": "text",
                "text": response,
                "response": response,
                "metadata": {}
            }
        
        # Check if response is a list (n8n returns array format)
        if isinstance(response, list):
            logger.debug(f"Response is a list with {len(response)} items")
            if len(response) > 0:
                # Take the first item
                first_item = response[0]
                # If it has an output field, extract from there
                if isinstance(first_item, dict) and "output" in first_item:
                    output = first_item["output"]
                    if isinstance(output, dict):
                        # Extract response text from output
                        text = output.get("response") or output.get("text") or output.get("message", "")
                        return {
                            "type": "text",
                            "text": text,
                            "response": text,
                            "metadata": output
                        }
                # Otherwise try to parse the first item directly
                return self._parse_response(first_item)
            else:
                logger.warning("N8N returned empty array")
                return {"type": "error", "error": "Empty response array from n8n"}
        
        # Log the raw response for debugging if it's a dict
        if isinstance(response, dict):
            try:
                logger.debug(f"Raw n8n response: {json.dumps(response, indent=2)}")
            except (TypeError, ValueError) as e:
                logger.debug(f"Raw n8n response (can't serialize): {response}")
        
        if isinstance(response, dict) and "error" in response:
            return {
                "type": "error",
                "error": response.get("error"),
                "message": response.get("message", "An error occurred")
            }
        
        if isinstance(response, dict) and "tool_calls" in response:
            return {
                "type": "tool_calls",
                "tool_calls": response["tool_calls"],
                "text": response.get("text", ""),
                "response": response.get("response", "")
            }
        
        # Check for various response formats (only if response is a dict)
        if isinstance(response, dict) and ("text" in response or "message" in response or "response" in response or "output" in response or "result" in response):
            text = (response.get("text") or 
                   response.get("message") or 
                   response.get("response") or 
                   response.get("output") or 
                   response.get("result", ""))
            return {
                "type": "text",
                "text": text,
                "response": response.get("response", text),
                "metadata": response.get("metadata", {})
            }
        
        # If response is a dict with any keys, try to extract text from them
        if isinstance(response, dict) and response:
            # Try to find any text-like field
            for key in ["content", "answer", "reply", "data"]:
                if key in response:
                    value = response[key]
                    if isinstance(value, str):
                        return {
                            "type": "text",
                            "text": value,
                            "response": value,
                            "metadata": response
                        }
        
        logger.warning(f"Unknown response format from n8n: {response}")
        return {
            "type": "unknown",
            "data": response
        }