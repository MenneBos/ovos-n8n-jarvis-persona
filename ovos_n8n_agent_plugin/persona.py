import asyncio
from typing import Optional, Dict, Any, List
from ovos_plugin_manager.templates.persona import Persona
from ovos_utils.log import LOG
from .n8n_client import N8NClient
from .command_processor import CommandProcessor

logger = LOG.create_logger(__name__)


class N8NJarvisPersona(Persona):
    """
    JARVIS Persona implementation using n8n workflows
    Processes all queries through n8n webhook for AI agent handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 bus=None, lang="en-us"):
        """Initialize JARVIS persona with n8n integration"""
        
        # Set persona name and description
        name = config.get("name", "JARVIS")
        description = config.get("description", 
                               "Just A Rather Very Intelligent System - Tony Stark's AI assistant")
        
        super().__init__(name=name, description=description, config=config, 
                        bus=bus, lang=lang)
        
        # Initialize n8n client and command processor
        self.n8n_client = N8NClient(self.config)
        self.command_processor = CommandProcessor(self.config)
        
        # Configuration options
        self.enable_streaming = self.config.get("enable_streaming", True)
        self.process_tools = self.config.get("process_tools", True)
        self.return_text_only = self.config.get("return_text_only", False)
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        
        # Override solver to avoid FailureSolver issues
        self.solvers = []  # Don't use any external solvers
        
        logger.info(f"N8N JARVIS Persona initialized with webhook: {self.n8n_client.webhook_url}")
    
    def match(self, utterance: str, lang: str = None, message=None) -> Optional[float]:
        """
        Determine if this persona should handle the utterance
        Returns confidence score (0.0 to 1.0) or None
        """
        # If configured as primary persona, always match with high confidence
        if self.config.get("primary_persona", True):
            return 0.95
        
        # Otherwise, only match if utterance contains wake words or triggers
        wake_words = self.config.get("wake_words", ["jarvis", "hey jarvis"])
        utterance_lower = utterance.lower()
        
        for wake_word in wake_words:
            if wake_word in utterance_lower:
                return 0.9
        
        # If fallback is enabled, provide low confidence match
        if self.fallback_enabled:
            return 0.3
        
        return None
    
    def get_response(self, utterance: str, lang: str = None, 
                    message=None, context: Optional[Dict] = None) -> Optional[str]:
        """
        Get response from n8n webhook
        This is the main method that processes queries
        """
        try:
            logger.debug(f"Processing utterance: {utterance}")
            
            # Build context from message if available
            if message and not context:
                context = {
                    "skill_id": message.context.get("skill_id"),
                    "source": message.context.get("source"),
                    "destination": message.context.get("destination")
                }
            
            # Send to n8n webhook
            response = self.n8n_client.send_query_sync(utterance, context)
            
            if response.get("type") == "error":
                error_msg = response.get('error', 'Unknown error')
                logger.error(f"N8N error: {error_msg}")
                
                # Handle specific error types
                if "404" in str(error_msg) or "not found" in error_msg.lower():
                    logger.error(f"N8N webhook not found at: {self.n8n_client.webhook_url}")
                    if not self.fallback_enabled:
                        return "Sir, I'm unable to connect to my primary systems. The webhook appears to be offline."
                elif "timeout" in error_msg.lower():
                    if not self.fallback_enabled:
                        return "Sir, the response is taking longer than expected. Please try again."
                elif not self.fallback_enabled:
                    return "I apologize Sir, but I'm experiencing technical difficulties."
                return None
            
            # Process tool calls if enabled
            if response.get("type") == "tool_calls" and self.process_tools:
                tool_results = self._process_tool_calls(response.get("tool_calls", []))
                
                # Get the JARVIS response text
                text_response = response.get("response") or response.get("text", "")
                
                if self.return_text_only:
                    return text_response or tool_results.get("message", "Action completed successfully, Sir.")
                else:
                    # Return JARVIS response, tool results are handled separately
                    return text_response
            
            # Handle text response
            if response.get("type") == "text":
                return response.get("text", "") or response.get("response", "")
            
            # Handle direct response field (from webhook)
            if "response" in response:
                return response["response"]
            
            logger.warning(f"Unknown response type: {response.get('type')}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing utterance: {e}", exc_info=True)
            if not self.fallback_enabled:
                return "I'm afraid I'm experiencing a system error, Sir."
            return None
    
    def get_response_streaming(self, utterance: str, lang: str = None,
                             message=None, context: Optional[Dict] = None):
        """
        Stream response from n8n webhook
        Yields response chunks as they arrive
        """
        if not self.enable_streaming:
            # Fall back to non-streaming
            response = self.get_response(utterance, lang, message, context)
            if response:
                yield response
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _stream():
                accumulated_text = ""
                tool_calls_buffer = []
                
                async for response in self.n8n_client.stream_query(utterance, context):
                    if response.get("type") == "error":
                        logger.error(f"Stream error: {response.get('error')}")
                        break
                    
                    if response.get("type") == "tool_calls":
                        tool_calls_buffer.extend(response.get("tool_calls", []))
                        
                        # Stream any text that comes with tool calls
                        text = response.get("response") or response.get("text", "")
                        if text and text != accumulated_text:
                            new_text = text[len(accumulated_text):]
                            accumulated_text = text
                            yield new_text
                    
                    elif response.get("type") == "text":
                        text = response.get("text", "") or response.get("response", "")
                        if text and text != accumulated_text:
                            new_text = text[len(accumulated_text):]
                            accumulated_text = text
                            yield new_text
                
                # Process tool calls after streaming
                if tool_calls_buffer and self.process_tools:
                    tool_results = self._process_tool_calls(tool_calls_buffer)
                    if not accumulated_text and tool_results.get("message"):
                        yield tool_results["message"]
            
            for chunk in loop.run_until_complete(_stream().__aiter__()):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield "I'm experiencing streaming difficulties, Sir."
    
    def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process tool calls from n8n response"""
        results = []
        
        for tool_call in tool_calls:
            try:
                result = self.command_processor.process_command(tool_call)
                results.append(result)
                
                # Emit message bus events for tool results if bus is available
                if self.bus and result.get("success"):
                    self._emit_tool_event(tool_call, result)
                    
            except Exception as e:
                logger.error(f"Error processing tool call: {e}", exc_info=True)
                results.append({
                    "success": False,
                    "error": str(e),
                    "tool": tool_call.get("tool"),
                    "action": tool_call.get("action")
                })
        
        # Return summary of results
        if results:
            successful = [r for r in results if r.get("success")]
            if successful:
                return {
                    "success": True,
                    "message": successful[0].get("message", "Action completed"),
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "error": results[0].get("error", "Action failed"),
                    "results": results
                }
        
        return {"success": True, "message": "No actions to perform"}
    
    def _emit_tool_event(self, tool_call: Dict, result: Dict):
        """Emit message bus event for tool execution"""
        if not self.bus:
            return
        
        event_type = f"ovos.persona.jarvis.tool.{tool_call.get('tool')}"
        event_data = {
            "tool": tool_call.get("tool"),
            "action": tool_call.get("action"),
            "params": tool_call.get("params", {}),
            "result": result
        }
        
        self.bus.emit(self.bus.message(event_type, event_data))
    
    def get_spoken_answer(self, query: str, context: Optional[Dict] = None, lang: Optional[str] = None):
        """
        Get spoken answer for a query - implements solver interface
        This method is called by the OVOS framework
        """
        return self.get_response(query, lang, context=context)
    
    def stream_utterance(self, query: str, context: Optional[Dict] = None, lang: Optional[str] = None):
        """
        Stream response - implements solver streaming interface
        Yields response chunks as they arrive
        """
        if self.enable_streaming:
            yield from self.get_response_streaming(query, lang, context=context)
        else:
            response = self.get_response(query, lang, context=context)
            if response:
                yield response
    
    @property
    def priority(self) -> int:
        """Return priority for this persona solver"""
        return 100 if self.config.get("primary_persona", True) else 50
    
    def shutdown(self):
        """Clean up resources"""
        try:
            if hasattr(self.n8n_client, 'close'):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.n8n_client.close())
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        super().shutdown()