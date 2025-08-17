"""N8N ChatMessageSolver for OVOS"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from ovos_plugin_manager.templates.solvers import ChatMessageSolver
from ovos_utils.log import LOG
from .n8n_client import N8NClient
from .command_processor import CommandProcessor

logger = LOG.create_logger(__name__)


class N8NJarvisSolver(ChatMessageSolver):
    """
    ChatMessageSolver that processes queries through n8n webhook
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 translator=None, detector=None, priority=100,
                 enable_tx=False, enable_cache=True, 
                 internal_lang=None):
        """Initialize N8N solver with n8n integration"""
        
        # Pass all parameters to parent class normally
        super().__init__(config=config, translator=translator, 
                        detector=detector, priority=priority,
                        enable_tx=enable_tx, enable_cache=enable_cache,
                        internal_lang=internal_lang)
        
        # Initialize n8n client and command processor
        self.n8n_client = N8NClient(self.config)
        self.command_processor = CommandProcessor(self.config)
        
        # Configuration options
        self.enable_streaming = self.config.get("enable_streaming", True)
        self.process_tools = self.config.get("process_tools", True)
        self.return_text_only = self.config.get("return_text_only", False)
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        
        logger.info(f"N8N Solver initialized with webhook: {self.n8n_client.webhook_url}")
    
    def get_chat_completion(self, messages: List[Dict[str, str]], 
                           lang: str = "en-US") -> str:
        """
        Main method for ChatMessageSolver - processes chat messages
        """
        # Extract the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            return "I didn't receive a message to process, Sir."
        
        # Process through n8n
        response = self.get_response(user_message, lang=lang)
        return response or "I'm unable to process that request at the moment, Sir."
    
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
                
                # Let fallback solvers handle if enabled
                return None
            
            # Process tool calls if enabled
            if self.process_tools and response.get("type") == "tool_calls":
                tool_result = self._process_tool_calls(response.get("tool_calls", []))
                
                # Return tool message or text response
                if tool_result.get("message"):
                    return tool_result["message"]
                elif response.get("text"):
                    return response["text"]
                elif response.get("response"):
                    return response["response"]
            
            # Return text response
            if response.get("type") == "text":
                return response.get("text") or response.get("response", "")
            
            # Handle unknown response type
            logger.warning(f"Unknown response type: {response.get('type')}")
            logger.debug(f"Full unknown response: {response}")
            
            # Try to extract any useful text from the response
            if response.get("data"):
                data = response["data"]
                # If data is a string, return it
                if isinstance(data, str):
                    return data
                # If data is a dict, try to find any text field
                if isinstance(data, dict):
                    for key in ["text", "message", "response", "output", "result", "content", "answer"]:
                        if key in data:
                            value = data[key]
                            if isinstance(value, str):
                                return value
                    # If no text field found, return the whole dict as string
                    return json.dumps(data)
            
            return response.get("text") or response.get("response") or response.get("message")
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            if not self.fallback_enabled:
                return "I'm experiencing an internal error, Sir. Please try again."
            return None
    
    def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process tool calls from n8n response"""
        results = []
        
        for tool_call in tool_calls:
            try:
                result = self.command_processor.process_command(tool_call)
                results.append(result)
                    
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
    
    def shutdown(self):
        """Cleanup when shutting down"""
        try:
            # Close async session if exists
            if hasattr(self.n8n_client, 'close'):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.n8n_client.close())
                loop.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")