import asyncio
from typing import Optional, Dict, Any, List
from ovos_plugin_manager.templates.solvers import QuestionSolver
from ovos_utils.log import LOG
from .n8n_client import N8NClient
from .command_processor import CommandProcessor

logger = LOG.create_logger(__name__)


class N8NAgentSolver(QuestionSolver):
    enable_tx = True
    priority = 100
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        
        self.n8n_client = N8NClient(self.config)
        self.command_processor = CommandProcessor(self.config)
        
        self.enable_streaming = self.config.get("enable_streaming", True)
        self.process_tools = self.config.get("process_tools", True)
        self.return_text_only = self.config.get("return_text_only", False)
        
        logger.info(f"N8NAgentSolver initialized with webhook: {self.n8n_client.webhook_url}")
    
    def get_spoken_answer(self, query: str, context: Optional[Dict] = None) -> Optional[str]:
        try:
            logger.debug(f"Processing query: {query}")
            
            response = self.n8n_client.send_query_sync(query, context)
            
            if response.get("type") == "error":
                logger.error(f"N8N error: {response.get('error')}")
                return None
            
            if response.get("type") == "tool_calls" and self.process_tools:
                tool_results = self._process_tool_calls(response.get("tool_calls", []))
                
                if self.return_text_only:
                    text_response = response.get("text", "")
                    if text_response:
                        return text_response
                    elif tool_results.get("success"):
                        return tool_results.get("message", "Action completed successfully")
                    else:
                        return f"Failed to execute action: {tool_results.get('error', 'Unknown error')}"
                else:
                    return response.get("text", "") or tool_results.get("message", "")
            
            if response.get("type") == "text":
                return response.get("text", "")
            
            logger.warning(f"Unknown response type: {response.get('type')}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return None
    
    def stream_utterances(self, query: str, context: Optional[Dict] = None):
        if not self.enable_streaming:
            answer = self.get_spoken_answer(query, context)
            if answer:
                yield answer
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _stream():
                accumulated_text = ""
                tool_calls_buffer = []
                
                async for response in self.n8n_client.stream_query(query, context):
                    if response.get("type") == "error":
                        logger.error(f"Stream error: {response.get('error')}")
                        break
                    
                    if response.get("type") == "tool_calls":
                        tool_calls_buffer.extend(response.get("tool_calls", []))
                        
                        text = response.get("text", "")
                        if text and text != accumulated_text:
                            new_text = text[len(accumulated_text):]
                            accumulated_text = text
                            yield new_text
                    
                    elif response.get("type") == "text":
                        text = response.get("text", "")
                        if text and text != accumulated_text:
                            new_text = text[len(accumulated_text):]
                            accumulated_text = text
                            yield new_text
                
                if tool_calls_buffer and self.process_tools:
                    tool_results = self._process_tool_calls(tool_calls_buffer)
                    if not accumulated_text and tool_results.get("message"):
                        yield tool_results["message"]
            
            for utterance in loop.run_until_complete(_stream()):
                yield utterance
                
        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
        finally:
            loop.close()
    
    def _process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        errors = []
        
        for tool_call in tool_calls:
            try:
                result = self.command_processor.process_command(tool_call)
                results.append(result)
                
                if not result.get("success"):
                    errors.append(result.get("error", "Unknown error"))
                    
            except Exception as e:
                logger.error(f"Error processing tool call {tool_call}: {e}", exc_info=True)
                errors.append(str(e))
        
        if errors:
            return {
                "success": False,
                "error": "; ".join(errors),
                "results": results
            }
        
        successful_actions = [r.get("action", "action") for r in results if r.get("success")]
        if successful_actions:
            message = f"Completed: {', '.join(successful_actions)}"
        else:
            message = "Actions processed"
        
        return {
            "success": True,
            "message": message,
            "results": results
        }
    
    def shutdown(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.n8n_client.close())
            loop.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")