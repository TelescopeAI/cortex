"""Jobs server starter for Plombery background tasks"""
import uvicorn
from plombery import get_app
from cortex.jobs.registry import register_all_pipelines


def start_jobs_server(
    host: str = "0.0.0.0",
    port: int = 9003,
    reload: bool = False
):
    """Start the Plombery jobs server"""
    # Register all pipelines
    app = register_all_pipelines()
    
    # Start server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

