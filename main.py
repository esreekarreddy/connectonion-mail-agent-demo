"""
Gmail Agent HTTP Server for deployment.

Purpose: Deploy Gmail Agent as HTTP server on ConnectOnion Cloud
Usage: co deploy (uses this file as entrypoint)
"""

from dotenv import load_dotenv

load_dotenv()

from agent import get_agent
from connectonion import host

agent = get_agent()
host(agent, trust="strict")
