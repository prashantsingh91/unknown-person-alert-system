#!/usr/bin/env python3
"""
Wrapper script to start uvicorn with CUDA libraries in LD_LIBRARY_PATH
This ensures GPU support works correctly for InsightFace
"""
import os
import sys
import site
import subprocess
from pathlib import Path

def setup_cuda_environment():
    """Set up LD_LIBRARY_PATH to include all NVIDIA CUDA libraries"""
    site_packages = site.getsitepackages()[0]
    
    # Find all nvidia library directories (recursively search nvidia* for lib dirs)
    nvidia_lib_dirs = []
    site_packages_path = Path(site_packages)
    
    # Search all nvidia* directories recursively for lib folders
    for nvidia_dir in site_packages_path.glob("nvidia*"):
        for lib_dir in nvidia_dir.rglob("lib"):
            if lib_dir.is_dir():
                nvidia_lib_dirs.append(str(lib_dir))
    
    if nvidia_lib_dirs:
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        new_ld_path = ':'.join(nvidia_lib_dirs)
        if current_ld_path:
            new_ld_path = f"{new_ld_path}:{current_ld_path}"
        
        os.environ['LD_LIBRARY_PATH'] = new_ld_path
        
        print("🔧 CUDA libraries configured:")
        for lib_dir in nvidia_lib_dirs:
            if 'cudnn' in lib_dir or 'cublas' in lib_dir:
                print(f"  ✓ {lib_dir}")
        return True
    else:
        print("⚠️  No NVIDIA CUDA libraries found")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting Backend with GPU Support")
    print("=" * 50)
    
    # Setup CUDA environment
    cuda_available = setup_cuda_environment()
    
    if cuda_available:
        print("✅ GPU support enabled")
    else:
        print("⚠️  Running in CPU mode")
    
    print("")
    
    # Start uvicorn with the updated environment
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8001"
    ]
    
    # Run uvicorn as a subprocess (inherits environment variables)
    subprocess.run(cmd)

