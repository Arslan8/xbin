# xbin

A blackboard-style orchestrator and SDK for binary analysis workers.

## Features

- **Consensus Engine**: Orchestrates multiple analysis backends (gRPC workers) with weighted confidence scoring.
- **Conflict Resolution**: Automatically identifies and flags conflicting symbol hypotheses.
- **Python SDK**: High-level `@xbin.plugin` decorator to turn any analysis tool into an xbin worker in minutes.
- **Agentic API**: REST endpoints for AI agents or humans to monitor and resolve global state.

## Installation

It is strongly recommended to install `xbin` inside a Python virtual environment to avoid dependency conflicts.

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

### From Source
```bash
git clone https://github.com/your-repo/xbin.git
cd xbin
pip install .
```

### For Development (Editable Mode)
```bash
pip install -e .
```

## Quick Start

### 1. Start the Orchestrator
The orchestrator will automatically attempt to start a Redis container via Docker if it's not already running.

```bash
xbin-orchestrator
```
### 2. Create a Plugin
Using the `xbin` SDK, you can create a new worker with minimal boilerplate.

#### Example: FLIRT Matcher
We've included a FLIRT signature matcher in `plugins/flirt`. To use it:

1. Install `python-flirt`:
   ```bash
   pip install python-flirt
   ```
2. Place IDA `.sig` files in a `signatures/` directory.
3. Run the worker:
   ```bash
   python plugins/flirt/flirt_worker.py
   ```

#### Custom Plugin Code
```python
import xbin
...
```
@xbin.plugin(name="my_analyzer", version="1.0")
def my_analysis_logic(task: xbin.TaskContext):
    # Perform analysis on task.address and task.raw_bytes
    return xbin.Match(symbol="secret_function", confidence=0.88)

if __name__ == "__main__":
    xbin.start_worker()
```

### 3. Monitor Results
Access the REST API to see active tools and function states:

```bash
# List active workers
curl http://localhost:8000/api/v1/tools

# Check the state of a function
curl http://localhost:8000/api/v1/functions/0x401000/state
```

## Architecture

- **`xbin-orchestrator`**: The central gRPC/REST server that manages the "blackboard".
- **`xbin` SDK**: A lightweight Python library for building worker plugins.
- **Redis**: Used as the high-performance backend for the blackboard state.

## License
MIT
