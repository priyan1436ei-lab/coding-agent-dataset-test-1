"""Standard development and inspection tools for AetherCoder agent."""
import glob
import json
import os
import re
import subprocess
from typing import Dict, Any, List, Optional

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents with optional start_line and end_line bounds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to view."},
                    "start_line": {"type": "integer", "description": "1-indexed start line."},
                    "end_line": {"type": "integer", "description": "1-indexed end line."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite file contents on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to target file."},
                    "content": {"type": "string", "description": "Full file content to write."},
                    "overwrite": {"type": "boolean", "description": "Allow overwriting existing file."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for text or regex query across directory files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search string or pattern."},
                    "directory": {"type": "string", "description": "Root directory to search in.", "default": "."},
                    "file_pattern": {"type": "string", "description": "File glob pattern.", "default": "*"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command with a strict timeout in an isolated process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command string to execute."},
                    "timeout_seconds": {"type": "integer", "description": "Execution timeout limit.", "default": 10}
                },
                "required": ["command"]
            }
        }
    }
]

def tool_read_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File does not exist: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        total_lines = len(lines)
        start = max(1, start_line or 1) - 1
        end = min(total_lines, end_line or total_lines)
        content = "".join(lines[start:end])
        return {
            "path": path,
            "total_lines": total_lines,
            "showing_lines": f"{start + 1}-{end}",
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}

def tool_write_file(path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if os.path.exists(path) and not overwrite:
            return {"error": f"File already exists: {path}"}
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "SUCCESS", "path": path, "bytes_written": len(content.encode("utf-8"))}
    except Exception as e:
        return {"error": str(e)}

def tool_search_files(query: str, directory: str = ".", file_pattern: str = "*") -> Dict[str, Any]:
    matches = []
    pattern = re.compile(query, re.IGNORECASE)
    for root, _, files in os.walk(directory):
        if any(ignore in root for ignore in [".git", "__pycache__", "node_modules", "data"]):
            continue
        for fname in files:
            if not glob.fnmatch.fnmatch(fname, file_pattern):
                continue
            full_path = os.path.join(root, fname)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for lno, line in enumerate(f, 1):
                        if pattern.search(line):
                            matches.append({"file": full_path, "line": lno, "text": line.strip()})
                            if len(matches) >= 50:
                                return {"matches": matches, "truncated": True}
            except Exception:
                pass
    return {"matches": matches, "truncated": False}

def tool_run_command(command: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    # Security guardrails against destructive operations
    blocked_commands = ["rm -rf /", "format c:", "mkfs", "dd if="]
    for b in blocked_commands:
        if b in command.lower():
            return {"error": f"BLOCKED_UNSAFE_COMMAND: {b}"}

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[:2000],
            "stderr": proc.stderr[:2000]
        }
    except subprocess.TimeoutExpired:
        return {"command": command, "error": f"Execution timed out after {timeout_seconds}s"}
    except Exception as e:
        return {"command": command, "error": str(e)}

def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call to appropriate handler."""
    if tool_name == "read_file":
        return tool_read_file(**arguments)
    elif tool_name == "write_file":
        return tool_write_file(**arguments)
    elif tool_name == "search_files":
        return tool_search_files(**arguments)
    elif tool_name == "run_command":
        return tool_run_command(**arguments)
    else:
        return {"error": f"Unknown tool: {tool_name}"}
