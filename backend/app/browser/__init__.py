"""
JARVIS Browser Automation Module

Provides browser automation for joining and managing virtual meetings.
"""

from app.browser.browser_manager import BrowserManager
from app.browser.google_meet import GoogleMeetAutomation

__all__ = ["BrowserManager", "GoogleMeetAutomation"]
