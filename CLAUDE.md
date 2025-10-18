# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ComfyUI is a powerful node-based workflow system for Stable Diffusion and other AI models. It uses a graph/nodes/flowchart interface where users design pipelines by connecting nodes. The system executes workflows asynchronously, caching results and only re-executing parts that change between runs.

## Running ComfyUI

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# For NVIDIA GPUs (recommended)
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu129
```

### Starting the Server
```bash
# Basic startup
python main.py

# Common options
python main.py --listen 0.0.0.0 --port 8188  # Listen on all interfaces
python main.py --cpu  # CPU-only mode (no GPU)
python main.py --preview-method taesd  # High-quality previews
python main.py --disable-all-custom-nodes  # Disable custom nodes
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not inference"  # Skip slow inference tests
pytest -m execution  # Only execution tests
pytest tests-unit/  # Only unit tests
```

## Architecture

### Execution Flow

The core execution model follows this flow:
1. **main.py** initializes the system, loads custom nodes, and starts the server
2. **server.py** (PromptServer) handles HTTP/WebSocket connections and manages the prompt queue
3. **execution.py** (PromptExecutor) executes workflow graphs node-by-node
4. **nodes.py** contains built-in node definitions (CLIPTextEncode, KSampler, etc.)

The execution system is **asynchronous** and **incremental**:
- Only nodes that changed (or depend on changed nodes) are re-executed
- Results are cached in one of three cache types: Classic, LRU, or Dependency-Aware
- A worker thread (`prompt_worker` in main.py) continuously processes the prompt queue

### Directory Structure

**Core Systems:**
- `comfy/` - Core library containing model loading, sampling, CLIP, VAE, ControlNet, LoRA, etc.
  - `model_management.py` - GPU/CPU memory management and model offloading
  - `samplers.py` - Diffusion sampling algorithms
  - `sd.py` - Checkpoint loading and model detection
  - `cli_args.py` - Command-line argument definitions
- `comfy_execution/` - Execution engine (graph traversal, caching, validation)
  - `graph.py` - Dynamic prompt graph representation
  - `caching.py` - Output caching strategies
  - `progress.py` - Progress tracking and reporting
- `comfy_api/` - API node system (for versioned public APIs)
- `comfy_extras/` - Built-in extra nodes loaded at startup
- `execution.py` - Main execution orchestrator (PromptExecutor)
- `nodes.py` - Built-in node definitions

**Server & API:**
- `server.py` - Main HTTP/WebSocket server (aiohttp-based)
- `api_server/` - Internal API routes
- `app/` - Application managers (user, models, custom nodes, frontend, database)
- `middleware/` - HTTP middleware (caching, compression, CORS)

**User-Facing Directories:**
- `models/` - Model files organized by type (checkpoints, loras, vae, controlnet, etc.)
- `custom_nodes/` - User-installed custom node packages
- `input/` - Input files (images, videos, etc.)
- `output/` - Generated outputs
- `user/` - User-specific settings and data

**Frontend:**
- `web/` - Compiled frontend (TypeScript/Vue from separate ComfyUI_frontend repo)
- Frontend is updated fortnightly; use `--front-end-version Comfy-Org/ComfyUI_frontend@latest` for daily builds

### Custom Nodes System

Custom nodes are Python packages in `custom_nodes/` that extend ComfyUI's functionality:

1. **Discovery**: On startup, `nodes.py:init_extra_nodes()` scans `custom_nodes/` directory
2. **Loading**: Each subdirectory is treated as a Python module
   - `prestartup_script.py` (optional) - Runs before PyTorch is imported
   - `__init__.py` - Main entry point, should define `NODE_CLASS_MAPPINGS` dict
3. **Registration**: Nodes register by adding to `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`
4. **Disable/Enable**: Add `.disabled` suffix to directory name or use `--disable-all-custom-nodes`

Custom node example structure:
```python
NODE_CLASS_MAPPINGS = {
    "MyCustomNode": MyCustomNodeClass
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyCustomNode": "My Custom Node"
}
```

### Model Loading & Management

**Model Search Paths:**
- Configured in `folder_paths.py` with `folder_names_and_paths` dict
- Default locations: `models/checkpoints/`, `models/loras/`, etc.
- Override with `extra_model_paths.yaml` or `--extra-model-paths-config`
- Use `--base-directory` to change the root models directory

**Model Management:**
- `comfy.model_management` handles loading/unloading models to manage VRAM
- Smart memory management can run models on GPUs with as low as 1GB VRAM
- Models are automatically offloaded when memory is needed
- Use `--cache-lru N` for LRU caching with N items

### Server Architecture

**Communication:**
- HTTP API for synchronous requests (upload, queue management, model info)
- WebSocket for real-time updates (execution progress, previews, completions)
- Binary protocol (`protocol.py`) for efficient image transfer

**Key Routes (server.py):**
- `/prompt` - Submit workflow for execution
- `/queue` - Queue management
- `/history` - Execution history
- `/object_info` - Node definitions and input types
- WebSocket at `/ws` - Real-time event streaming

**Authentication:**
- Optional user management via `app/user_manager.py`
- Database support for users and settings (SQLAlchemy + Alembic)

### Graph Execution Model

Workflows are represented as JSON with node IDs and connections:
```json
{
  "node_id": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["1", 0],  // [source_node_id, output_index]
      "seed": 12345
    }
  }
}
```

**Execution Process:**
1. Workflow submitted via `/prompt` API
2. Graph validation (`comfy_execution/validation.py`)
3. Dependency resolution and execution order determination
4. Node-by-node execution with caching
5. Progress updates via WebSocket
6. Results stored in `PromptExecutor.outputs`

**Caching Strategies:**
- Classic: Cache by node ID and inputs
- LRU: Least Recently Used eviction
- Dependency-Aware: Smart invalidation based on graph dependencies

### Node Development

Nodes are Python classes with specific structure:

```python
class MyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_name": ("TYPE", {"default": value})
            }
        }

    RETURN_TYPES = ("OUTPUT_TYPE",)
    FUNCTION = "execute"  # Method name to call
    CATEGORY = "category/subcategory"

    def execute(self, input_name):
        # Process inputs and return outputs as tuple
        return (result,)
```

**New API Style (comfy_api):**
- Use `ComfyNodeABC` base class for versioned API support
- Use `IO.*` constants for type definitions (IO.IMAGE, IO.LATENT, etc.)
- Supports `INPUT_TOOLTIPS`, `OUTPUT_TOOLTIPS`, and `DESCRIPTION`

## Development Commands

### Model Paths
```bash
# Use custom model paths
python main.py --extra-model-paths-config /path/to/extra_model_paths.yaml

# Change output directory
python main.py --output-directory /path/to/outputs
```

### GPU Configuration
```bash
# Select specific CUDA device
python main.py --cuda-device 0

# Force precision settings
python main.py --fp16-unet  # Run diffusion model in fp16
python main.py --fp32-vae   # Run VAE in fp32
```

### Performance
```bash
# Enable LRU caching (keep 10 recent outputs)
python main.py --cache-lru 10

# CPU-only mode
python main.py --cpu

# AMD ROCm optimizations
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 python main.py --use-pytorch-cross-attention
```

### Development
```bash
# Quick CI test (exits immediately after startup)
python main.py --quick-test-for-ci

# Disable custom nodes for debugging
python main.py --disable-all-custom-nodes

# Enable specific custom nodes
python main.py --disable-all-custom-nodes --whitelist-custom-nodes my-node-name
```

## Important Files

- **folder_paths.py** - Central registry of model search paths and file discovery
- **execution.py** - Core execution loop, the heart of workflow processing
- **server.py** - HTTP/WebSocket server and API endpoints
- **main.py** - Entry point, initialization, and startup sequence
- **nodes.py** - All built-in node definitions
- **comfy/model_management.py** - VRAM management and model loading/unloading
- **comfy/sd.py** - Checkpoint detection and loading logic
- **extra_model_paths.yaml.example** - Example configuration for shared model paths

## Release Cycle

ComfyUI follows a weekly release cycle (typically Friday). Three interconnected repositories:
1. **ComfyUI Core** (this repo) - Backend and node system
2. **ComfyUI Desktop** - Desktop application wrapper
3. **ComfyUI Frontend** - TypeScript/Vue frontend (updated fortnightly in core)

## Common Patterns

### Finding Models
```python
import folder_paths
checkpoints = folder_paths.get_filename_list("checkpoints")
loras = folder_paths.get_filename_list("loras")
```

### Registering Custom Nodes
```python
# In custom_nodes/my_pack/__init__.py
NODE_CLASS_MAPPINGS = {
    "MyNode": MyNodeClass
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode": "My Custom Node Display Name"
}
```

### Progress Hooks
```python
from comfy.utils import ProgressBar
pbar = ProgressBar(total_steps)
for i in range(total_steps):
    pbar.update(1)
```

## Database

ComfyUI includes optional SQLAlchemy-based database:
- **app/database/db.py** - Database initialization
- **alembic_db/** - Database migrations
- Run `alembic upgrade head` for schema updates

## Troubleshooting

### Import torch before main.py
If you see "Torch already imported" warning, some code is importing PyTorch before main.py sets environment variables. This can break CUDA device selection and memory allocation.

### Custom nodes not loading
- Check for `.disabled` suffix on directory
- Verify `NODE_CLASS_MAPPINGS` is defined in `__init__.py`
- Check logs for import errors (missing dependencies)
- Use `--disable-all-custom-nodes --whitelist-custom-nodes node-name` to isolate issues

### CUDA malloc errors
Run with `--disable-cuda-malloc` if you get CUDA malloc errors on older GPUs.

### Black VAE outputs
Use `--fp32-vae` to run VAE in full precision if you get black images.
