@echo off
rem Starts an MCP server from the repo root, with the tools from mise.toml (uv/uvx, Python 3.12).
rem Calls mise by its full path so it works even when the process PATH has no shims.
cd /d "%~dp0.."
"%LOCALAPPDATA%\Microsoft\WinGet\Links\mise.exe" x -- %*
