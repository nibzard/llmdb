#!/usr/bin/env bash
uvicorn mcp_server.server:create_app --factory --reload
