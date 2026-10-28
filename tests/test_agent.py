"""Automated unit tests for agent tools and execution runtime."""
import os
import pytest
from src.agent.tools import tool_read_file, tool_write_file, tool_search_files, tool_run_command, execute_tool_call
from src.agent.agent_runtime import AetherCoderAgent

def test_tool_write_and_read(tmp_path):
    test_f = str(tmp_path / "sample.txt")
    write_res = tool_write_file(test_f, "line 1\nline 2\nline 3\n")
    assert write_res.get("status") == "SUCCESS"

    read_res = tool_read_file(test_f, start_line=2, end_line=3)
    assert "line 2\nline 3" in read_res["content"]

def test_tool_search_files():
    res = tool_search_files(query="def ", directory="src", file_pattern="*.py")
    assert len(res["matches"]) > 0

def test_tool_run_command_blocks_malicious():
    res = tool_run_command("rm -rf /")
    assert "error" in res
    assert "BLOCKED_UNSAFE_COMMAND" in res["error"]

def test_agent_step_loop():
    agent = AetherCoderAgent()
    outcome = agent.run_step_loop("Check project structure")
    assert outcome["total_steps"] >= 2
    assert "analyzed successfully" in outcome["final_response"]
