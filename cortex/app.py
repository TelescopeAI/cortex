"""Unified launcher for Cortex API and Jobs servers"""
import multiprocessing
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CortexDataApp:
    """Unified application launcher for API and Jobs servers
    
    Design:
    - Jobs server is opt-in (only starts when CORTEX_ENABLE_JOBS=true or using GCS)
    - Uses multiprocessing.Process ONLY when starting both servers
    - Direct execution when starting single server (better logging in cloud)
    - Multiprocessing enables proper vCPU utilization for heavy workloads
    
    For production, deploy as separate services for best scalability.
    """
    
    def __init__(
        self,
        api_host: str = "0.0.0.0",
        api_port: int = 9002,
        jobs_host: str = "0.0.0.0",
        jobs_port: int = 9003,
        reload: bool = False,
        start_api: bool = True,
        start_jobs: bool = False  # False by default, opt-in
    ):
        self.api_host = api_host
        self.api_port = api_port
        self.jobs_host = jobs_host
        self.jobs_port = jobs_port
        self.reload = reload
        self.start_api = start_api
        self.start_jobs = start_jobs
    
    def start(self):
        """Start API and/or Jobs servers
        
        Strategy:
        - Both servers: Use multiprocessing for parallel execution
        - Single server: Direct execution for better cloud logging
        """
        # Case 1: Start both servers - use multiprocessing
        if self.start_api and self.start_jobs:
            self._start_with_multiprocessing()
        
        # Case 2: Start only API server - direct execution
        elif self.start_api:
            logger.info(f"Starting API server on {self.api_host}:{self.api_port}")
            from cortex.api.main import start_api_server
            start_api_server(
                host=self.api_host,
                port=self.api_port,
                reload=self.reload
            )
        
        # Case 3: Start only Jobs server - direct execution
        elif self.start_jobs:
            logger.info(f"Starting Jobs server on {self.jobs_host}:{self.jobs_port}")
            from cortex.jobs.server import start_jobs_server
            start_jobs_server(
                host=self.jobs_host,
                port=self.jobs_port,
                reload=self.reload
            )
        
        else:
            logger.warning("No servers configured to start. Set start_api=True or start_jobs=True")
    
    def _start_with_multiprocessing(self):
        """Start both servers using multiprocessing for vCPU utilization"""
        logger.info("Starting both API and Jobs servers with multiprocessing")
        
        from cortex.api.main import start_api_server
        from cortex.jobs.server import start_jobs_server
        
        # Start API server in separate process
        api_process = multiprocessing.Process(
            target=start_api_server,
            kwargs={
                "host": self.api_host,
                "port": self.api_port,
                "reload": self.reload
            },
            name="CortexAPIServer"
        )
        
        # Start Jobs server in separate process
        jobs_process = multiprocessing.Process(
            target=start_jobs_server,
            kwargs={
                "host": self.jobs_host,
                "port": self.jobs_port,
                "reload": self.reload
            },
            name="CortexJobsServer"
        )
        
        api_process.start()
        jobs_process.start()
        
        # Wait for both processes
        api_process.join()
        jobs_process.join()


def create_data_app(**kwargs) -> CortexDataApp:
    """Factory function to create Cortex Data App
    
    The start_jobs parameter is determined automatically:
    - Enabled if CORTEX_ENABLE_JOBS=true
    - Enabled if CORTEX_FILE_STORAGE_TYPE=gcs (needs cache eviction)
    - Disabled otherwise (default)
    
    Examples:
        # Default: API only
        app = create_data_app()
        app.start()
        
        # Enable jobs explicitly
        app = create_data_app(start_jobs=True)
        app.start()
    """
    from cortex.core.config.execution_env import ExecutionEnv
    
    # Auto-determine if jobs should be enabled
    if 'start_jobs' not in kwargs:
        enable_jobs = ExecutionEnv.get_key("CORTEX_ENABLE_JOBS", "false").lower() == "true"
        storage_type = ExecutionEnv.get_key("CORTEX_FILE_STORAGE_TYPE", "local").lower()
        
        # Enable jobs if explicitly requested OR using GCS (needs cache eviction)
        kwargs['start_jobs'] = enable_jobs or (storage_type == "gcs")
    
    return CortexDataApp(**kwargs)
