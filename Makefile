.PHONY: dev

dev:
	lsof -ti tcp:8765 | xargs kill -9 2>/dev/null; python3 webui/server.py
