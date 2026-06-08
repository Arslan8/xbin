import pytest
import subprocess
import time
import redis
import os
import sys

# Ensure src is in path for tests
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

@pytest.fixture(scope="session", autouse=True)
def orchestrator_server():
    """Start the xbin Orchestrator in the background for integration testing."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src:src/xbin_orchestrator"
    
    # Start orchestrator process
    proc = subprocess.Popen(
        [sys.executable, "-m", "xbin_orchestrator.main"], 
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for the gRPC server to bind and become ready
    time.sleep(2) 
    
    yield
    
    # Teardown
    proc.terminate()
    proc.wait()

@pytest.fixture(autouse=True)
def clean_redis():
    """Ensure a clean Redis state before every test."""
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.flushdb()
    yield r
