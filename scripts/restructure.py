import os
import shutil
from pathlib import Path

def create_directory_structure():
    # Base directories
    dirs = [
        "src/core",
        "src/utils/llm_providers",
        "src/utils/services",
        "src/spaces/newsroom/agents",
        "src/spaces/newsroom/scenes",
        "src/spaces/newsroom/data",
        "src/spaces/newsroom/examples",
        "src/spaces/newsroom/transcripts",
        "src/spaces/newsroom/audio_outputs",
    ]
    
    # Create directories
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        Path(dir_path) / "__init__.py"
    
    # Create .gitkeep files for empty directories
    Path("src/spaces/newsroom/transcripts/.gitkeep").touch()
    Path("src/spaces/newsroom/audio_outputs/.gitkeep").touch()

def remove_legacy_files():
    # Directories to remove
    legacy_dirs = [
        "ai_newsroom",
        "examples",
        "agents_arena",
    ]
    
    for dir_path in legacy_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

def main():
    # Remove legacy structure
    remove_legacy_files()
    
    # Create new structure
    create_directory_structure()
    
    print("Directory restructuring completed!")

if __name__ == "__main__":
    main() 