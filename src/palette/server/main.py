"""
Main FastAPI application for Palette Intelligence Server
Serves as the entry point for uvicorn and provides the unified API
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator
import asyncio
import uuid
import json
from datetime import datetime
import subprocess
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Add src to Python path
project_root = Path(__file__).parent.parent.parent.parent  # Go up to Palette root
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from palette.analysis.context import ProjectAnalyzer
from palette.conversation.conversation_engine import ConversationEngine
from palette.quality.validator import ComponentValidator

# Import fallback wrapper for analysis methods
try:
    from .analysis_wrapper import AnalysisWrapper
except ImportError:
    # Fallback for when running as script directly
    from analysis_wrapper import AnalysisWrapper


# Pydantic models for API requests/responses
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    python_version: str


class GenerationRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    projectPath: str
    conversationHistory: Optional[List[Dict]] = None
    requestMetadata: Optional[Dict] = None


class AnalysisRequest(BaseModel):
    projectPath: str
    analysisType: Optional[str] = "full"  # "full", "quick", "frameworks", "quality", "components", "design_tokens"


class QualityValidationRequest(BaseModel):
    projectPath: str
    filePaths: List[str]  # Files to validate
    code: Optional[str] = None  # Code content for inline validation
    validationType: Optional[str] = "comprehensive"  # "comprehensive", "syntax", "imports", "types"


class RouteRequest(BaseModel):
    projectPath: str
    route: str
    component: str
    importPath: str
    label: Optional[str] = None
    appPath: Optional[str] = "src/App.tsx"
    navigationPath: Optional[str] = "src/components/Navigation.tsx"
    index: Optional[bool] = False


class RouteRemovalRequest(BaseModel):
    projectPath: str
    route: str
    appPath: Optional[str] = "src/App.tsx"
    navigationPath: Optional[str] = "src/components/Navigation.tsx"
    removeFromNavigation: Optional[bool] = True


class RouteAnalysisRequest(BaseModel):
    projectPath: str
    appPath: Optional[str] = "src/App.tsx"
    navigationPath: Optional[str] = "src/components/Navigation.tsx"


class StreamEvent(BaseModel):
    event: str
    data: Dict
    id: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="Palette Intelligence Server",
    description="AI-powered design prototyping intelligence layer for VS Code",
    version="0.6.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "vscode-webview://*",
        "https://*",
        "http://localhost:*",
        "http://127.0.0.1:*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_streams: Dict[str, asyncio.Queue] = {}
conversation_engines: Dict[str, ConversationEngine] = {}
project_analyzers: Dict[str, ProjectAnalyzer] = {}


def get_or_create_analyzer(project_path: str) -> ProjectAnalyzer:
    """Get or create a project analyzer for the given path"""
    if project_path not in project_analyzers:
        analyzer = ProjectAnalyzer()
        # Set the project path for analysis
        analyzer.project_path = project_path
        
        # Add missing methods from wrapper as fallback
        wrapper = AnalysisWrapper(project_path)
        if not hasattr(analyzer, 'detect_framework'):
            analyzer.detect_framework = wrapper.detect_framework
        if not hasattr(analyzer, 'detect_styling_library'):
            analyzer.detect_styling_library = wrapper.detect_styling_library
        if not hasattr(analyzer, 'has_typescript'):
            analyzer.has_typescript = wrapper.has_typescript
        if not hasattr(analyzer, 'detect_tailwind'):
            analyzer.detect_tailwind = wrapper.detect_tailwind
        if not hasattr(analyzer, 'detect_build_tool'):
            analyzer.detect_build_tool = wrapper.detect_build_tool
        if not hasattr(analyzer, 'detect_package_manager'):
            analyzer.detect_package_manager = wrapper.detect_package_manager
        
        project_analyzers[project_path] = analyzer
    return project_analyzers[project_path]


def get_or_create_engine(project_path: str) -> ConversationEngine:
    """Get or create a conversation engine for the given path"""
    if project_path not in conversation_engines:
        conversation_engines[project_path] = ConversationEngine(project_path)
    return conversation_engines[project_path]


async def send_stream_event(conversation_id: str, event_type: str, data: Dict) -> None:
    """Send an event to a stream if it exists"""
    if conversation_id in active_streams:
        event = StreamEvent(
            event=event_type,
            data=data,
            id=str(uuid.uuid4())
        )
        await active_streams[conversation_id].put(event)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.6.0",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


@app.post("/api/analyze")
async def analyze_project(request: AnalysisRequest):
    """Analyze project structure, frameworks, and dependencies"""
    try:
        analyzer = get_or_create_analyzer(request.projectPath)
        
        if request.analysisType == "quick":
            # Quick analysis - just framework detection
            result = {
                "framework": analyzer.detect_framework(),
                "styling": analyzer.detect_styling_library(),
                "hasTypeScript": analyzer.has_typescript(),
                "timestamp": datetime.now().isoformat()
            }
        elif request.analysisType == "frameworks":
            # Framework-focused analysis
            result = {
                "framework": analyzer.detect_framework(),
                "styling": analyzer.detect_styling_library(),
                "hasTypeScript": analyzer.has_typescript(),
                "hasTailwind": analyzer.detect_tailwind(),
                "buildTool": analyzer.detect_build_tool(),
                "packageManager": analyzer.detect_package_manager(),
                "timestamp": datetime.now().isoformat()
            }
        elif request.analysisType == "components":
            # Component-focused analysis
            analysis_result = analyzer.analyze_project(request.projectPath)
            components_data = analysis_result.get("components", {})
            result = {
                "totalComponents": len(components_data.get("files", [])),
                "componentsByType": components_data.get("by_type", {}),
                "reusableComponents": components_data.get("reusable", []),
                "pageComponents": components_data.get("pages", []),
                "uiLibraryComponents": components_data.get("ui_library", []),
                "customComponents": components_data.get("custom", []),
                "componentPatterns": components_data.get("patterns", {}),
                "timestamp": datetime.now().isoformat()
            }
        elif request.analysisType == "design_tokens":
            # Design tokens and theming analysis
            analysis_result = analyzer.analyze_project(request.projectPath)
            design_data = analysis_result.get("design_tokens", {})
            result = {
                "colorPalette": design_data.get("colors", {}),
                "typography": design_data.get("typography", {}),
                "spacing": design_data.get("spacing", {}),
                "breakpoints": design_data.get("breakpoints", {}),
                "customCss": design_data.get("custom_css", []),
                "tailwindConfig": design_data.get("tailwind_config", {}),
                "designSystem": design_data.get("design_system", {}),
                "timestamp": datetime.now().isoformat()
            }
        elif request.analysisType == "quality":
            # Quality analysis - validation and suggestions
            try:
                validator = ComponentValidator(request.projectPath)
                quality_result = validator.validate_project_quality()
                result = {
                    "qualityScore": quality_result.get("score", 0),
                    "issues": quality_result.get("issues", []),
                    "suggestions": quality_result.get("suggestions", []),
                    "codeMetrics": quality_result.get("metrics", {}),
                    "bestPractices": quality_result.get("best_practices", {}),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                # Fallback if ComponentValidator fails
                result = {
                    "qualityScore": 75,  # Default reasonable score
                    "issues": [f"Quality analysis partially failed: {str(e)}"],
                    "suggestions": ["Enable comprehensive quality checking", "Ensure all dependencies are installed"],
                    "timestamp": datetime.now().isoformat()
                }
        else:
            # Full analysis - comprehensive project understanding
            analysis_result = analyzer.analyze_project(request.projectPath)
            result = {
                "framework": analysis_result.get("framework", "unknown"),
                "styling": analysis_result.get("styling", "unknown"),
                "hasTypeScript": analysis_result.get("typescript", False),
                "hasTailwind": analysis_result.get("tailwind", False),
                "components": analysis_result.get("components", {}),
                "structure": analysis_result.get("structure", {}),
                "dependencies": analysis_result.get("dependencies", {}),
                "designTokens": analysis_result.get("design_tokens", {}),
                "codebaseInsights": {
                    "totalFiles": len(analysis_result.get("structure", {}).get("files", [])),
                    "linesOfCode": analysis_result.get("metrics", {}).get("total_lines", 0),
                    "complexity": analysis_result.get("metrics", {}).get("complexity", "medium"),
                    "maintainability": analysis_result.get("metrics", {}).get("maintainability", "good")
                },
                "recommendations": analysis_result.get("recommendations", []),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "analysis": result,
            "analysisType": request.analysisType,
            "projectPath": request.projectPath,
            "cacheKey": f"{request.projectPath}_{request.analysisType}_{int(datetime.now().timestamp())}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/generate/stream")
async def start_generation(request: GenerationRequest):
    """Start a new generation with streaming response"""
    conversation_id = request.conversationId or str(uuid.uuid4())
    
    # Create stream queue
    active_streams[conversation_id] = asyncio.Queue()
    
    # Start generation in background
    asyncio.create_task(process_generation(request, conversation_id))
    
    return {
        "conversationId": conversation_id,
        "streamUrl": f"/api/generate/stream/{conversation_id}",
        "status": "started"
    }


@app.get("/api/generate/stream/{conversation_id}")
async def stream_generation(conversation_id: str):
    """Server-Sent Events endpoint for streaming generation results"""
    if conversation_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return EventSourceResponse(sse_generator(conversation_id))


async def sse_generator(conversation_id: str) -> AsyncGenerator[Dict, None]:
    """Generate Server-Sent Events for a conversation"""
    try:
        queue = active_streams[conversation_id]
        
        # Send connection established event
        yield {
            "event": "connected",
            "data": json.dumps({
                "conversationId": conversation_id,
                "timestamp": datetime.now().isoformat()
            }),
            "id": str(uuid.uuid4())
        }
        
        # Process events from queue
        while True:
            try:
                # Wait for next event with timeout for keepalive
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                if event is None:  # End of stream
                    break
                
                # Send the event
                yield {
                    "event": event.event,
                    "data": json.dumps(event.data),
                    "id": event.id or str(uuid.uuid4())
                }
                
                # Check for completion
                if event.event in ["complete", "error"]:
                    break
                    
            except asyncio.TimeoutError:
                # Send keepalive to prevent connection timeout
                yield {
                    "event": "keepalive",
                    "data": json.dumps({"timestamp": datetime.now().isoformat()}),
                    "id": str(uuid.uuid4())
                }
                
    except Exception as e:
        # Send error event
        yield {
            "event": "error",
            "data": json.dumps({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }),
            "id": str(uuid.uuid4())
        }
    finally:
        # Cleanup
        if conversation_id in active_streams:
            del active_streams[conversation_id]


async def process_generation(request: GenerationRequest, conversation_id: str):
    """Process generation request asynchronously with enhanced multi-file support"""
    try:
        # Send analysis phase start
        await send_stream_event(conversation_id, "analysis_start", {
            "phase": "analyzing_project",
            "message": "Understanding your project structure..."
        })
        
        # Perform project analysis first
        analyzer = get_or_create_analyzer(request.projectPath)
        analysis_result = analyzer.analyze_project(request.projectPath)
        
        # Send analysis complete with detailed info
        await send_stream_event(conversation_id, "analysis_complete", {
            "phase": "analysis_complete",
            "message": "Project analysis complete, starting generation...",
            "analysis": {
                "framework": analysis_result.get("framework", "unknown"),
                "styling": analysis_result.get("styling", "unknown"),
                "components": len(analysis_result.get("component_patterns", {}).get("files", [])),
                "hasTypeScript": analyzer.has_typescript(),
                "hasTailwind": analyzer.detect_tailwind()
            }
        })
        
        # Classify request complexity
        is_complex = any(keyword in request.message.lower() for keyword in [
            "page", "dashboard", "complete", "multi", "feature", "app", "site"
        ])
        
        if is_complex:
            await send_stream_event(conversation_id, "complexity_detected", {
                "complexity": "high",
                "message": "Complex request detected - enabling multi-file generation",
                "features": ["multi-file", "project-analysis", "quality-assurance"]
            })
        
        # Send generation start
        await send_stream_event(conversation_id, "generation_start", {
            "phase": "generating_code", 
            "message": "Generating your design...",
            "estimated_files": 3 if is_complex else 1
        })
        
        # Prepare conversation history with analysis context
        history = []
        if request.conversationHistory:
            for msg in request.conversationHistory:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
        
        # Add analysis context to history
        analysis_context = f"""
Project Analysis Context:
- Framework: {analysis_result.get("framework", "unknown")}
- Styling: {analysis_result.get("styling", "unknown")}
- TypeScript: {analyzer.has_typescript()}
- Tailwind: {analyzer.detect_tailwind()}
- Components Available: {len(analysis_result.get("component_patterns", {}).get("files", []))}
"""
        
        history.insert(0, {
            'role': 'system',
            'content': analysis_context
        })
        
        # Enhanced streaming callback with file tracking
        files_generated = []
        current_file = None
        
        async def enhanced_stream_callback(chunk: str, metadata: Optional[Dict] = None):
            nonlocal current_file, files_generated
            
            # Check if this chunk indicates a new file
            if metadata and metadata.get("file_path"):
                if current_file != metadata["file_path"]:
                    current_file = metadata["file_path"]
                    files_generated.append(current_file)
                    
                    await send_stream_event(conversation_id, "file_start", {
                        "file_path": current_file,
                        "file_type": metadata.get("file_type", "component"),
                        "file_index": len(files_generated)
                    })
            
            await send_stream_event(conversation_id, "generation_chunk", {
                "content": chunk,
                "file_path": current_file,
                "metadata": metadata or {}
            })
            
            # Check if file is complete
            if metadata and metadata.get("file_complete"):
                await send_stream_event(conversation_id, "file_complete", {
                    "file_path": current_file,
                    "lines": metadata.get("lines", 0),
                    "size": len(chunk) if chunk else 0
                })
        
        # Get or create conversation engine
        engine = get_or_create_engine(request.projectPath)
        
        # Process the message - this will be run in a thread pool
        def sync_process():
            def sync_callback(chunk: str, metadata: Optional[Dict] = None):
                # Schedule the async callback
                asyncio.create_task(enhanced_stream_callback(chunk, metadata))
            
            return engine.process_message(
                request.message,
                history,
                sync_callback
            )
        
        # Run in thread pool to avoid blocking
        result = await asyncio.to_thread(sync_process)
        
        # Perform quality validation for complex requests
        quality_results = None
        if is_complex and files_generated:
            await send_stream_event(conversation_id, "quality_start", {
                "phase": "quality_validation",
                "message": "Validating generated code quality...",
                "files": files_generated
            })
            
            try:
                validator = ComponentValidator(request.projectPath)
                quality_results = validator.validate_files(files_generated, validation_type="comprehensive")
                
                quality_score = quality_results.get("score", 0)
                quality_issues = quality_results.get("issues", [])
                
                await send_stream_event(conversation_id, "quality_complete", {
                    "phase": "quality_complete",
                    "message": f"Quality validation complete - Score: {quality_score}/100",
                    "score": quality_score,
                    "issues": len(quality_issues),
                    "critical_issues": len([i for i in quality_issues if i.get("severity") == "critical"]),
                    "suggestions": len(quality_results.get("suggestions", []))
                })
                
            except Exception as e:
                await send_stream_event(conversation_id, "quality_warning", {
                    "phase": "quality_warning", 
                    "message": f"Quality validation partially failed: {str(e)}",
                    "fallback_score": 75
                })
                quality_results = {"score": 75, "issues": [], "suggestions": []}
        
        # Send generation summary
        await send_stream_event(conversation_id, "generation_summary", {
            "files_generated": files_generated,
            "total_files": len(files_generated),
            "analysis_used": True,
            "quality_assured": is_complex,
            "quality_score": quality_results.get("score", 0) if quality_results else None
        })
        
        # Send completion
        await send_stream_event(conversation_id, "generation_complete", {
            "response": result.get('response', ''),
            "metadata": result.get('metadata', {}),
            "files": result.get('files', files_generated),
            "analysis": analysis_result,
            "success": True
        })
        
        # End stream
        await send_stream_event(conversation_id, "complete", {
            "conversationId": conversation_id,
            "total_files": len(files_generated),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Send error
        await send_stream_event(conversation_id, "error", {
            "error": str(e),
            "conversationId": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
    finally:
        # Signal end of stream
        if conversation_id in active_streams:
            await active_streams[conversation_id].put(None)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print("🎨 Palette Intelligence Server starting up...")
    print(f"📍 Project root: {project_root}")
    print(f"🐍 Python version: {sys.version}")
    
    # Verify required directories exist
    required_dirs = [
        src_path / "palette",
        src_path / "palette" / "analysis", 
        src_path / "palette" / "conversation",
        src_path / "palette" / "generation"
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"⚠️  Warning: Required directory not found: {dir_path}")
        else:
            print(f"✅ Found: {dir_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("🛑 Palette Intelligence Server shutting down...")
    
    # Cleanup active streams
    for conversation_id in list(active_streams.keys()):
        try:
            await active_streams[conversation_id].put(None)
        except:
            pass
    active_streams.clear()
    
    # Cleanup engines and analyzers
    conversation_engines.clear()
    project_analyzers.clear()
    
    print("✅ Cleanup completed")


# Additional utility endpoints
@app.get("/api/status")
async def get_status():
    """Get server status and statistics"""
    return {
        "server": "running",
        "activeStreams": len(active_streams),
        "conversationEngines": len(conversation_engines),
        "projectAnalyzers": len(project_analyzers),
        "uptime": datetime.now().isoformat(),
        "memoryUsage": {
            "streams": f"{len(active_streams)} active",
            "engines": f"{len(conversation_engines)} cached",
            "analyzers": f"{len(project_analyzers)} cached"
        }
    }


@app.post("/api/quality/validate")
async def validate_quality(request: QualityValidationRequest):
    """Validate code quality for specific files or code content"""
    try:
        validator = ComponentValidator(request.projectPath)
        
        if request.code:
            # Validate inline code content
            validation_result = validator.validate_code_content(
                request.code, 
                file_type=request.validationType
            )
        else:
            # Validate specific files
            validation_result = validator.validate_files(
                request.filePaths,
                validation_type=request.validationType
            )
        
        return {
            "success": True,
            "validation": validation_result,
            "validationType": request.validationType,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "overallScore": validation_result.get("score", 0),
                "criticalIssues": len([i for i in validation_result.get("issues", []) if i.get("severity") == "critical"]),
                "warnings": len([i for i in validation_result.get("issues", []) if i.get("severity") == "warning"]),
                "suggestions": len(validation_result.get("suggestions", []))
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "validation": {
                "score": 50,  # Default fallback score
                "issues": [{"type": "validation_error", "message": str(e), "severity": "warning"}],
                "suggestions": ["Ensure all dependencies are properly installed"]
            }
        }


@app.post("/api/mcp/shadcn")
async def generate_with_shadcn_mcp(request: GenerationRequest):
    """Generate UI components using shadcn/ui MCP server integration"""
    try:
        # This endpoint will integrate with our MCP shadcn/ui server
        # For now, we'll use the existing generation pipeline with enhanced shadcn awareness
        
        analyzer = get_or_create_analyzer(request.projectPath)
        analysis_result = analyzer.analyze_project(request.projectPath)
        
        # Check if project has shadcn/ui setup (simplified check)
        has_tailwind = analyzer.detect_tailwind()
        
        if not has_tailwind:
            return {
                "success": False,
                "error": "Project doesn't appear to have Tailwind CSS setup (required for shadcn/ui)",
                "suggestion": "Install Tailwind CSS and run 'npx shadcn-ui@latest init' to setup shadcn/ui first",
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if project has shadcn/ui setup properly
        has_shadcn = analyzer.detect_tailwind()  # Using Tailwind as proxy for shadcn setup
        
        # Enhanced generation with MCP-aware context
        enhanced_message = f"""
{request.message}

IMPORTANT: Use shadcn/ui components exclusively. Available components based on project analysis:
- Button, Card, Input, Badge, Dialog, Sheet, Dropdown, Select
- Focus on complete, interactive pages and features
- Use proper shadcn/ui import patterns: import {{ Button }} from "@/components/ui/button"
- Ensure components are properly styled with Tailwind CSS
- Generate complete pages that users can see and interact with
"""
        
        # Use existing generation pipeline with enhanced prompt
        enhanced_request = GenerationRequest(
            message=enhanced_message,
            conversationId=request.conversationId,
            projectPath=request.projectPath,
            conversationHistory=request.conversationHistory,
            requestMetadata={
                **(request.requestMetadata if request.requestMetadata else {}),
                "mcp_mode": "shadcn",
                "enhanced_shadcn": True
            }
        )
        
        # Start enhanced generation
        conversation_id = request.conversationId or str(uuid.uuid4())
        active_streams[conversation_id] = asyncio.Queue()
        
        # Process with MCP enhancements
        asyncio.create_task(process_mcp_generation(enhanced_request, conversation_id))
        
        return {
            "conversationId": conversation_id,
            "streamUrl": f"/api/generate/stream/{conversation_id}",
            "status": "started",
            "mcpMode": "shadcn",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP generation failed: {str(e)}")


@app.get("/api/mcp/components/available")
async def get_available_shadcn_components(project_path: str):
    """Get available shadcn/ui components in the project"""
    try:
        analyzer = get_or_create_analyzer(project_path)
        analysis_result = analyzer.analyze_project(project_path)
        
        # Extract available shadcn/ui components
        ui_components = analysis_result.get("components", {}).get("ui_library", [])
        
        # Common shadcn/ui components to check for
        common_shadcn_components = [
            "button", "card", "input", "label", "textarea", "select",
            "dialog", "sheet", "popover", "dropdown-menu", "navigation-menu",
            "tabs", "badge", "avatar", "table", "form", "checkbox", "radio-group",
            "switch", "slider", "progress", "separator", "skeleton", "toast"
        ]
        
        available_components = []
        for component in common_shadcn_components:
            # Check if component file exists
            component_file = Path(project_path) / "components" / "ui" / f"{component}.tsx"
            if component_file.exists():
                available_components.append({
                    "name": component,
                    "file": str(component_file),
                    "import": f'import {{ {component.title().replace("-", "")} }} from "@/components/ui/{component}"'
                })
        
        return {
            "success": True,
            "projectPath": project_path,
            "availableComponents": available_components,
            "totalComponents": len(available_components),
            "recommendation": "Install more shadcn/ui components with 'npx shadcn-ui@latest add'" if len(available_components) < 10 else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/mcp/preview/generate")
async def generate_preview_url(request: Dict):
    """Generate preview URL for generated components (integration with preview service)"""
    try:
        file_paths = request.get("filePaths", [])
        project_path = request.get("projectPath", "")
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="No file paths provided")
        
        # For now, return a mock preview URL structure
        # In the future, this would integrate with our preview service
        preview_data = {
            "previewId": str(uuid.uuid4()),
            "files": file_paths,
            "projectPath": project_path,
            "previewUrl": f"http://localhost:3000/preview/{str(uuid.uuid4())[:8]}",
            "qrCode": f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "expiresAt": (datetime.now() + asyncio.get_event_loop().time() + 3600).__str__(),
            "instructions": "Scan QR code or visit URL to see live preview",
            "status": "ready"
        }
        
        return {
            "success": True,
            "preview": preview_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


async def process_mcp_generation(request: GenerationRequest, conversation_id: str):
    """Enhanced generation process with MCP integrations"""
    try:
        # Send MCP mode notification
        await send_stream_event(conversation_id, "mcp_mode_active", {
            "mode": "shadcn",
            "message": "Enhanced shadcn/ui generation active",
            "features": ["component-analysis", "shadcn-optimization", "preview-generation"]
        })
        
        # Run the standard generation process
        await process_generation(request, conversation_id)
        
    except Exception as e:
        await send_stream_event(conversation_id, "error", {
            "error": f"MCP generation failed: {str(e)}",
            "conversationId": conversation_id,
            "timestamp": datetime.now().isoformat()
        })


@app.post("/api/context")
async def get_generation_context(request: AnalysisRequest):
    """Get project context optimized for AI generation (for Vercel AI SDK integration)"""
    try:
        analyzer = get_or_create_analyzer(request.projectPath)
        analysis_result = analyzer.analyze_project(request.projectPath)
        
        # Extract key context for AI generation
        components_data = analysis_result.get("components", {})
        design_data = analysis_result.get("design_tokens", {})
        
        # Build context optimized for AI prompts
        context = {
            "project": {
                "path": request.projectPath,
                "framework": analyzer.detect_framework(),
                "styling": analyzer.detect_styling_library(), 
                "hasTypeScript": analyzer.has_typescript(),
                "hasTailwind": analyzer.detect_tailwind(),
                "hasShadcnUI": len(components_data.get("ui_library", [])) > 0
            },
            "existingComponents": {
                "total": len(components_data.get("files", [])),
                "uiLibrary": components_data.get("ui_library", []),
                "custom": components_data.get("custom", []),
                "pages": components_data.get("pages", []),
                "patterns": components_data.get("patterns", {})
            },
            "designSystem": {
                "colors": design_data.get("colors", {}),
                "spacing": design_data.get("spacing", {}),
                "typography": design_data.get("typography", {}),
                "tailwindConfig": design_data.get("tailwind_config", {}),
                "customCss": design_data.get("custom_css", [])
            },
            "fileStructure": {
                "componentsDir": "src/components",
                "pagesDir": "src/pages", 
                "uiDir": "src/components/ui",
                "utilsDir": "src/lib"
            },
            "recommendations": {
                "useExisting": [comp for comp in components_data.get("reusable", [])],
                "importPatterns": [
                    'import { Button } from "@/components/ui/button"',
                    'import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"',
                    'import { cn } from "@/lib/utils"'
                ],
                "bestPractices": [
                    "Always use shadcn/ui components when available",
                    "Use design tokens instead of hardcoded colors",
                    "Follow existing component patterns",
                    "Ensure TypeScript compatibility" if analyzer.has_typescript() else "Generate JavaScript code"
                ]
            },
            "meta": {
                "analysisTimestamp": datetime.now().isoformat(),
                "cacheKey": f"{request.projectPath}_{int(datetime.now().timestamp())}"
            }
        }
        
        return {
            "success": True,
            "context": context,
            "projectPath": request.projectPath
        }
        
    except Exception as e:
        # Fallback context for when analysis fails
        return {
            "success": False,
            "error": str(e),
            "context": {
                "project": {
                    "path": request.projectPath,
                    "framework": "unknown", 
                    "styling": "unknown",
                    "hasTypeScript": True,
                    "hasTailwind": True,
                    "hasShadcnUI": True
                },
                "recommendations": {
                    "bestPractices": [
                        "Use shadcn/ui components",
                        "Generate with TypeScript",
                        "Use Tailwind CSS classes",
                        "Follow React best practices"
                    ]
                },
                "meta": {
                    "analysisTimestamp": datetime.now().isoformat(),
                    "fallback": True
                }
            }
        }


@app.post("/api/routes/analyze")
async def analyze_routes(request: RouteAnalysisRequest):
    """Analyze existing React Router routes in the project"""
    try:
        mcp_server_path = project_root / "mcp-servers" / "react-router" / "dist" / "server.js"
        
        # Check if MCP server is built
        if not mcp_server_path.exists():
            # Try to build it
            build_result = await build_mcp_server()
            if not build_result["success"]:
                raise HTTPException(status_code=500, detail=f"MCP server build failed: {build_result['error']}")
        
        # Call MCP server to analyze routes
        result = await call_mcp_tool("analyze_routes", {
            "appPath": request.appPath
        }, str(request.projectPath))
        
        return {
            "success": True,
            "routes": result,
            "projectPath": request.projectPath,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/routes/add")
async def add_route(request: RouteRequest):
    """Add a new route to React Router configuration"""
    try:
        # Direct file manipulation approach (bypass MCP for now)
        app_path = Path(request.projectPath) / request.appPath
        nav_path = Path(request.projectPath) / request.navigationPath
        
        results = []
        
        # Add route to App.tsx
        if app_path.exists():
            content = app_path.read_text()
            
            # Determine if this is a named or default export by checking the file
            import_path = Path(request.projectPath) / (request.importPath.replace('./', 'src/') + '.tsx')
            is_named_export = False
            
            if import_path.exists():
                file_content = import_path.read_text()
                # Check for named export pattern
                if f'export const {request.component}' in file_content or f'export {{ {request.component} }}' in file_content:
                    is_named_export = True
            
            # Create appropriate import line based on export type
            if is_named_export:
                import_line = f'import {{ {request.component} }} from "{request.importPath}";'
            else:
                import_line = f'import {request.component} from "{request.importPath}";'
            
            if import_line not in content:
                # Find the last import and add after it
                lines = content.split('\n')
                import_index = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('import '):
                        import_index = i
                
                if import_index >= 0:
                    lines.insert(import_index + 1, import_line)
                    content = '\n'.join(lines)
            
            # Prepare route with correct nesting and JSX syntax
            # Use relative path for nested routes (no leading slash)
            relative_route = request.route.lstrip("/") if request.route != "/" else ""
            
            # Check if route already exists
            route_exists = False
            if request.index or relative_route == "":
                route_exists = '<Route index element=' in content
            else:
                route_exists = f'<Route path="{relative_route}"' in content
                
            if not route_exists:
                # Find the Layout route section for proper nesting
                layout_start = content.find('<Route path="/" element={<Layout />}>')
                if layout_start != -1:
                    # Find all nested routes inside Layout using a more precise pattern
                    nested_pattern = r'          <Route (?:index|path="[^"]*") element=\{<[^>]+>\} />'
                    nested_routes = list(re.finditer(nested_pattern, content))
                    
                    # Filter to only routes that are actually inside the Layout
                    layout_routes = []
                    layout_end = content.find('        </Route>', layout_start)
                    for route_match in nested_routes:
                        if layout_start < route_match.start() < layout_end:
                            layout_routes.append(route_match)
                    
                    if layout_routes:
                        # Insert after the last nested route inside Layout
                        last_route = layout_routes[-1]
                        insertion_point = last_route.end()
                        if request.index or relative_route == "":
                            new_route = f'\n          <Route index element={{<{request.component} />}} />'
                        else:
                            new_route = f'\n          <Route path="{relative_route}" element={{<{request.component} />}} />'
                        content = content[:insertion_point] + new_route + content[insertion_point:]
                    else:
                        # No nested routes yet, add first one
                        layout_end = content.find('        </Route>', layout_start)
                        if layout_end != -1:
                            if request.index or relative_route == "":
                                new_route = f'\n          <Route index element={{<{request.component} />}} />\n        '
                            else:
                                new_route = f'\n          <Route path="{relative_route}" element={{<{request.component} />}} />\n        '
                            content = content[:layout_end] + new_route + content[layout_end:]
                else:
                    # Fallback: add at the end of Routes if no Layout found
                    if request.index or relative_route == "":
                        route_line = f'        <Route index element={{<{request.component} />}} />'
                    else:
                        route_line = f'        <Route path="{relative_route}" element={{<{request.component} />}} />'
                    content = content.replace('</Routes>', f'        {route_line}\n      </Routes>')
            
            app_path.write_text(content)
            results.append("Added route to App.tsx")
        
        # Skip automatic navigation updates - let users control their navigation
        # if request.label and nav_path.exists():
        #     [navigation update logic commented out for user flexibility]
        if request.label and nav_path.exists():
            # Only log that navigation update was skipped for user awareness
            results.append(f"Route added to App.tsx only. Navigation update skipped for user control.")
        
        return {
            "success": True,
            "route": {
                "path": request.route,
                "component": request.component,
                "importPath": request.importPath,
                "label": request.label
            },
            "results": results,
            "message": f"Added route {request.route} with component {request.component}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/routes/remove")
async def remove_route(request: RouteRemovalRequest):
    """Remove a route from React Router configuration"""
    try:
        mcp_server_path = project_root / "mcp-servers" / "react-router" / "dist" / "server.js"
        
        if not mcp_server_path.exists():
            build_result = await build_mcp_server()
            if not build_result["success"]:
                raise HTTPException(status_code=500, detail=f"MCP server build failed: {build_result['error']}")
        
        # Remove route via MCP server
        result = await call_mcp_tool("remove_route", {
            "route": request.route,
            "appPath": request.appPath,
            "removeFromNavigation": request.removeFromNavigation,
            "navigationPath": request.navigationPath
        }, str(request.projectPath))
        
        return {
            "success": True,
            "removedRoute": request.route,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.post("/api/routes/generate-config")
async def generate_route_config(request: RouteAnalysisRequest):
    """Generate complete route configuration based on page files"""
    try:
        mcp_server_path = project_root / "mcp-servers" / "react-router" / "dist" / "server.js"
        
        if not mcp_server_path.exists():
            build_result = await build_mcp_server()
            if not build_result["success"]:
                raise HTTPException(status_code=500, detail=f"MCP server build failed: {build_result['error']}")
        
        # Generate route config via MCP server
        result = await call_mcp_tool("generate_route_config", {
            "pagesDir": "src/pages",
            "appPath": request.appPath,
            "navigationPath": request.navigationPath
        }, str(request.projectPath))
        
        return {
            "success": True,
            "config": result,
            "projectPath": request.projectPath,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def build_mcp_server() -> Dict[str, any]:
    """Build the React Router MCP server"""
    try:
        mcp_dir = project_root / "mcp-servers" / "react-router"
        
        # Install dependencies if needed
        if not (mcp_dir / "node_modules").exists():
            install_process = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=str(mcp_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await install_process.communicate()
        
        # Build the server
        build_process = await asyncio.create_subprocess_exec(
            "npm", "run", "build",
            cwd=str(mcp_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await build_process.communicate()
        
        if build_process.returncode == 0:
            return {"success": True, "message": "MCP server built successfully"}
        else:
            return {"success": False, "error": stderr.decode() if stderr else "Build failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_mcp_tool(tool_name: str, arguments: Dict, project_path: str) -> Dict:
    """Call a tool from the React Router MCP server"""
    try:
        mcp_server_path = project_root / "mcp-servers" / "react-router" / "dist" / "server.js"
        
        # Prepare the MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Run the MCP server with the request
        process = await asyncio.create_subprocess_exec(
            "node", str(mcp_server_path),
            cwd=project_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Send request and get response
        request_json = json.dumps(mcp_request)
        print(f"🔧 Sending MCP request: {request_json}")
        stdout, stderr = await process.communicate(request_json.encode())
        
        print(f"🔧 MCP response - stdout: {stdout.decode()}")
        print(f"🔧 MCP response - stderr: {stderr.decode()}")
        print(f"🔧 MCP return code: {process.returncode}")
        
        if process.returncode != 0:
            raise Exception(f"MCP server error: {stderr.decode() if stderr else 'Unknown error'}")
        
        stdout_text = stdout.decode().strip()
        if not stdout_text:
            raise Exception("MCP server returned empty response")
        
        # Parse response
        response = json.loads(stdout_text)
        
        if "error" in response:
            raise Exception(f"MCP tool error: {response['error']}")
            
        return response.get("result", {})
        
    except Exception as e:
        raise Exception(f"Failed to call MCP tool {tool_name}: {str(e)}")


@app.delete("/api/cleanup")
async def cleanup_resources():
    """Clean up cached resources"""
    # Cleanup conversation engines and analyzers
    conversation_engines.clear()
    project_analyzers.clear()
    
    return {
        "message": "Resources cleaned up",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8765,
        reload=True,
        log_level="info"
    )