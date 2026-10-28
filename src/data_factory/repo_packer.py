"""Repository-level multi-file packager for cross-file dependency understanding."""
import os
import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("repo_packer")

MANIFEST_NAMES = {
    "requirements.txt", "setup.py", "pyproject.toml",
    "package.json", "tsconfig.json",
    "Cargo.toml", "Cargo.lock",
    "pom.xml", "build.gradle",
    "go.mod", "go.sum",
    "CMakeLists.txt", "Makefile",
    "Dockerfile", "docker-compose.yml"
}

def generate_file_tree(repo_dir: str, max_depth: int = 4) -> str:
    """Generate ASCII directory tree representation for LLM repository context."""
    tree_lines = []
    base_depth = repo_dir.rstrip(os.sep).count(os.sep)

    for root, dirs, files in os.walk(repo_dir):
        # Exclude version control and build caches
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", "target", "build", "dist"]]
        depth = root.count(os.sep) - base_depth
        if depth > max_depth:
            continue
        indent = "  " * depth
        folder_name = os.path.basename(root)
        if depth > 0:
            tree_lines.append(f"{indent}{folder_name}/")
        for f in sorted(files):
            if not f.endswith((".pyc", ".class", ".o", ".exe", ".png", ".jpg")):
                tree_lines.append(f"{indent}  {f}")
    return "\n".join(tree_lines[:100])

def pack_repository(
    repo_dir: str,
    repo_name: Optional[str] = None,
    max_total_chars: int = 64000
) -> Dict[str, Any]:
    """Pack an entire repository into a standardized multi-file context record."""
    if not os.path.exists(repo_dir):
        raise FileNotFoundError(f"Repository directory does not exist: {repo_dir}")

    name = repo_name or os.path.basename(os.path.abspath(repo_dir))
    tree = generate_file_tree(repo_dir)

    files_content = []
    manifests_found = []
    total_chars = 0

    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", "node_modules", "target", "build", "dist", ".pytest_cache"]]
        for fname in sorted(files):
            rel_path = os.path.relpath(os.path.join(root, fname), repo_dir).replace("\\", "/")
            if fname in MANIFEST_NAMES:
                manifests_found.append(rel_path)
            
            # Skip binary and very large files
            if fname.endswith((".pyc", ".o", ".bin", ".tar", ".gz", ".zip", ".png", ".jpg")):
                continue
            
            full_path = os.path.join(root, fname)
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if total_chars + len(content) > max_total_chars:
                    continue
                files_content.append({"path": rel_path, "content": content})
                total_chars += len(content)
            except Exception:
                pass

    # Construct unified repository representation
    repo_prompt = f"""<repo_context>
<repo_name>{name}</repo_name>
<manifests>{", ".join(manifests_found)}</manifests>
<file_tree>
{tree}
</file_tree>
"""
    for file_obj in files_content:
        repo_prompt += f"""<file_sep path="{file_obj['path']}">
{file_obj['content']}
</file_sep>
"""
    repo_prompt += "</repo_context>"

    return {
        "repo_name": name,
        "manifests": manifests_found,
        "files_count": len(files_content),
        "total_chars": len(repo_prompt),
        "formatted_context": repo_prompt
    }
