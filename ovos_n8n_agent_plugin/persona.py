import asyncio
from typing import Optional, Dict, Any, List
from ovos_plugin_manager.templates.solvers import ChatMessageSolver
from ovos_utils.log import LOG
from .n8n_client import N8NClient

logger = LOG.create_logger(__name__)


class N8NJarvisPersona(ChatMessageSolver):
    """
    JARVIS Persona implementation using n8n workflows
    Processes all queries through n8n webhook for AI agent handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 translator=None, detector=None, priority=100,
                 enable_tx=False, enable_cache=True, 
                 internal_lang=None):
        """Initialize JARVIS persona with n8n integration"""
        
        # Pass all parameters to parent class normally
        super().__init__(config=config, translator=translator, 
                        detector=detector, priority=priority,
                        enable_tx=enable_tx, enable_cache=enable_cache,
                        internal_lang=internal_lang)
        
        # Initialize n8n client
        self.n8n_client = N8NClient(self.config)
        
        # Configuration options
        self.enable_streaming = self.config.get("enable_streaming", True)
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        
        # Override solver to avoid FailureSolver issues
        self.solvers = []  # Don't use any external solvers
        
        logger.info(f"N8N JARVIS Persona initialized with webhook: {self.n8n_client.webhook_url}")
    
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
                return None
            
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
                
                async for response in self.n8n_client.stream_query(utterance, context):
                    if response.get("type") == "error":
                        logger.error(f"Stream error: {response.get('error')}")
                        break
                    
                    if response.get("type") == "text":
                        text = response.get("text", "") or response.get("response", "")
                        if text and text != accumulated_text:
                            new_text = text[len(accumulated_text):]
                            accumulated_text = text
                            yield new_text
            
            for chunk in loop.run_until_complete(_stream().__aiter__()):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield "I'm experiencing streaming difficulties, Sir."
    
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