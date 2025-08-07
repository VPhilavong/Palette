"""
Streaming HTTP Server for VS Code Extension Communication

This server provides HTTP endpoints with Server-Sent Events (SSE) streaming
for real-time communication between the VS Code extension and Palette backend.
"""

import json
import asyncio
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, AsyncGenerator, Any
from dataclasses import dataclass, asdict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..conversation.conversation_engine import ConversationEngine
from ..analysis.simple_vite_analyzer import SimpleViteAnalyzer


# Request/Response models
class GenerateRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    projectPath: str
    conversationHistory: Optional[list] = None


class AnalyzeRequest(BaseModel):
    projectPath: str


class StreamingResponse(BaseModel):
    conversationId: str
    streamUrl: str


@dataclass
class SSEEvent:
    """Server-Sent Event data structure"""
    type: str
    data: Any
    id: Optional[str] = None
    
    def to_sse_format(self) -> str:
        """Convert to SSE format string"""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to mark end of event
        return "\n".join(lines)


class StreamingServer:
    """HTTP server with SSE streaming for VS Code extension"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Palette Streaming Server")
        self.conversation_engine: Optional[ConversationEngine] = None
        self.analyzer: Optional[SimpleViteAnalyzer] = None
        
        # Active streaming connections
        self.active_streams: Dict[str, asyncio.Queue] = {}
        self.server_thread: Optional[threading.Thread] = None
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["vscode-webview://*", "https://*", "http://localhost:*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/analyze")
        async def analyze_project(request: AnalyzeRequest):
            """Analyze project structure and dependencies"""
            try:
                if not self.analyzer:
                    self.analyzer = SimpleViteAnalyzer()
                
                analysis = self.analyzer.analyze_project(request.projectPath)
                
                return {
                    "success": True,
                    "analysis": {
                        "framework": analysis.get("framework", "vite"),
                        "styling": analysis.get("styling", "tailwind"),
                        "hasTypeScript": analysis.get("typescript", True),
                        "hasTailwind": True,  # Always true for our Vite setup
                        "componentsPath": analysis.get("components_directory", "src/components"),
                        "pagesPath": None  # Vite doesn't have pages directory
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/generate")
        async def generate_component(request: GenerateRequest):
            """Start component generation with streaming response"""
            conversation_id = request.conversationId or str(uuid.uuid4())
            stream_url = f"http://{self.host}:{self.port}/api/stream/{conversation_id}"
            
            # Create async queue for this stream
            self.active_streams[conversation_id] = asyncio.Queue()
            
            # Start generation in background
            asyncio.create_task(self._generate_async(
                request.message,
                conversation_id,
                request.projectPath,
                request.conversationHistory or []
            ))
            
            return StreamingResponse(
                conversationId=conversation_id,
                streamUrl=stream_url
            )
        
        @self.app.get("/api/stream/{conversation_id}")
        async def stream_response(conversation_id: str):
            """SSE endpoint for streaming responses"""
            if conversation_id not in self.active_streams:
                raise HTTPException(status_code=404, detail="Stream not found")
            
            return StreamingResponse(
                self._sse_generator(conversation_id),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                }
            )
    
    async def _sse_generator(self, conversation_id: str) -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events for a conversation"""
        try:
            stream_queue = self.active_streams[conversation_id]
            
            # Send initial connection event
            initial_event = SSEEvent(
                type="status",
                data={"status": "connected", "conversationId": conversation_id},
                id=str(uuid.uuid4())
            )
            yield initial_event.to_sse_format()
            
            # Stream events from queue
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(stream_queue.get(), timeout=30.0)
                    
                    if event is None:  # Sentinel value to end stream
                        break
                        
                    yield event.to_sse_format()
                    
                    # Check if this is a completion event
                    if event.type == "complete":
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    keepalive = SSEEvent(type="keepalive", data={})
                    yield keepalive.to_sse_format()
                    
        except Exception as e:
            error_event = SSEEvent(
                type="error",
                data={"error": str(e)},
                id=str(uuid.uuid4())
            )
            yield error_event.to_sse_format()
        finally:
            # Cleanup
            if conversation_id in self.active_streams:
                del self.active_streams[conversation_id]
    
    async def _generate_async(self, message: str, conversation_id: str, project_path: str, history: list):
        """Generate component asynchronously and send events to stream"""
        try:
            if not self.conversation_engine:
                self.conversation_engine = ConversationEngine(project_path)
            
            stream_queue = self.active_streams.get(conversation_id)
            if not stream_queue:
                return
            
            # Send generation start event
            await stream_queue.put(SSEEvent(
                type="status",
                data={"status": "generating", "message": "Starting generation..."}
            ))
            
            # Convert history to proper format
            formatted_history = []
            for msg in history:
                formatted_history.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Generate with streaming callback
            def stream_callback(chunk: str, is_complete: bool = False):
                """Callback for streaming chunks"""
                event = SSEEvent(
                    type="chunk" if not is_complete else "complete",
                    data={
                        "content": chunk,
                        "conversationId": conversation_id,
                        "isComplete": is_complete
                    }
                )
                
                # Add to queue (this will be awaited in the SSE generator)
                try:
                    asyncio.create_task(stream_queue.put(event))
                except Exception as e:
                    print(f"Error adding to stream queue: {e}")
            
            # Start generation
            result = await asyncio.to_thread(
                self.conversation_engine.process_message,
                message,
                formatted_history,
                stream_callback
            )
            
            # Send completion event
            await stream_queue.put(SSEEvent(
                type="complete",
                data={
                    "response": result.get('response', ''),
                    "conversationId": conversation_id,
                    "metadata": result.get('metadata', {})
                }
            ))
            
            # Send sentinel to end stream
            await stream_queue.put(None)
            
        except Exception as e:
            # Send error event
            if conversation_id in self.active_streams:
                stream_queue = self.active_streams[conversation_id]
                await stream_queue.put(SSEEvent(
                    type="error",
                    data={"error": str(e), "conversationId": conversation_id}
                ))
                await stream_queue.put(None)  # End stream
    
    def start_server(self, background: bool = True):
        """Start the server"""
        if background:
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            return self.server_thread
        else:
            self._run_server()
    
    def _run_server(self):
        """Run the server (blocking)"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    
    def stop_server(self):
        """Stop the server"""
        # This is a simplified stop - in production you'd want proper shutdown
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
    
    @property
    def base_url(self) -> str:
        """Get the base URL of the server"""
        return f"http://{self.host}:{self.port}"


# Singleton instance
_server_instance: Optional[StreamingServer] = None


def get_streaming_server(host: str = "localhost", port: int = 8765) -> StreamingServer:
    """Get or create the streaming server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = StreamingServer(host, port)
    return _server_instance


def start_streaming_server(host: str = "localhost", port: int = 8765) -> StreamingServer:
    """Start the streaming server and return instance"""
    server = get_streaming_server(host, port)
    server.start_server(background=True)
    return server


if __name__ == "__main__":
    # For testing
    server = start_streaming_server()
    print(f"Streaming server started at {server.base_url}")
    
    try:
        # Keep main thread alive
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop_server()