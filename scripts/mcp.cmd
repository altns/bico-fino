@echo off
rem Inicia um servidor MCP a partir de C:\3D, com as ferramentas do mise.toml (uv/uvx, Python 3.12).
rem Chama o mise pelo caminho completo para funcionar mesmo quando o PATH do processo nao tem os shims.
cd /d "%~dp0.."
"%LOCALAPPDATA%\Microsoft\WinGet\Links\mise.exe" x -- %*
