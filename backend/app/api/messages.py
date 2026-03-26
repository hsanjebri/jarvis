"""
Message API Routes

Endpoints for message monitoring and summarization.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.agents.message_agent import message_agent

router = APIRouter()

@router.get("/summary")
async def get_messages_summary():
    """
    Get a summary of unread messages across all monitored platforms.
    """
    try:
        summary = await message_agent.get_unread_summary()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor/slack/{channel_id}")
async def monitor_slack_channel(channel_id: str):
    """
    Start monitoring a specific Slack channel.
    """
    return await message_agent.monitor_slack(channel_id)

@router.get("/platforms")
async def list_monitored_platforms():
    """
    List all communication platforms supported by JARVIS.
    """
    return {"platforms": message_agent.platforms}
