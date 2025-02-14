import os
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the new directory structure"""
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
    
    # Create directories and __init__.py files
    for dir_path in dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        (path / "__init__.py").touch()
    
    # Create .gitkeep files
    Path("src/spaces/newsroom/transcripts/.gitkeep").touch()
    Path("src/spaces/newsroom/audio_outputs/.gitkeep").touch()

def migrate_files():
    """Migrate files from old to new structure"""
    migrations = [
        # Core files
        ("ai_newsroom/agents/base.py", "src/core/base_agent.py"),
        
        # Utils
        ("ai_newsroom/utils/llm.py", "src/utils/llm_providers/openai.py"),
        ("ai_newsroom/services/tts.py", "src/utils/services/tts.py"),
        
        # Newsroom space
        ("ai_newsroom/agents/host.py", "src/spaces/newsroom/agents/host.py"),
        ("ai_newsroom/agents/analyst.py", "src/spaces/newsroom/agents/analyst.py"),
        ("ai_newsroom/agents/commenter.py", "src/spaces/newsroom/agents/commenter.py"),
        ("ai_newsroom/agents/seeker.py", "src/spaces/newsroom/agents/seeker.py"),
        ("ai_newsroom/spaces/podcast/podcast_space.py", "src/spaces/newsroom/scenes/podcast.py"),
        ("ai_newsroom/spaces/podcast/playbook.py", "src/spaces/newsroom/data/prompts.py"),
        ("examples/create_podcast.py", "src/spaces/newsroom/examples/create_podcast.py"),
    ]
    
    for src, dst in migrations:
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Migrated: {src} -> {dst}")

def remove_legacy_files():
    """Remove old directory structure"""
    legacy_dirs = [
        "ai_newsroom",
        "examples",
        "agents_arena",
        "transcripts",
        "audio_outputs",
    ]
    
    for dir_path in legacy_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"Removed: {dir_path}")

def main():
    # Create new structure
    create_directory_structure()
    print("Created new directory structure")
    
    # Migrate files
    migrate_files()
    print("Migrated files to new structure")
    
    # Remove legacy files
    remove_legacy_files()
    print("Removed legacy files")
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    main() 