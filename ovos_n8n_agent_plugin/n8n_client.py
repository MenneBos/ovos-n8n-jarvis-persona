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
            "Content-Type": "application/json"
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
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"N8N response: {result}")
            
            return self._parse_response(result)
            
        except requests.exceptions.Timeout:
            logger.error(f"N8N webhook timeout after {self.timeout} seconds")
            return {"error": "Request timeout", "type": "timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"N8N webhook request failed: {e}")
            return {"error": str(e), "type": "request_error"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse N8N response: {e}")
            return {"error": "Invalid JSON response", "type": "parse_error"}
    
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
            return {"error": "Request timeout", "type": "timeout"}
        except aiohttp.ClientError as e:
            logger.error(f"N8N webhook request failed: {e}")
            return {"error": str(e), "type": "request_error"}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse N8N response: {e}")
            return {"error": "Invalid JSON response", "type": "parse_error"}
    
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
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in response:
            return {
                "type": "error",
                "error": response.get("error"),
                "message": response.get("message", "An error occurred")
            }
        
        if "tool_calls" in response:
            return {
                "type": "tool_calls",
                "tool_calls": response["tool_calls"],
                "text": response.get("text", "")
            }
        
        if "text" in response or "message" in response:
            return {
                "type": "text",
                "text": response.get("text") or response.get("message", ""),
                "metadata": response.get("metadata", {})
            }
        
        return {
            "type": "unknown",
            "data": response
        }