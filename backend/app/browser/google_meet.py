"""
Google Meet Automation

Automates joining and managing Google Meet meetings.
"""

import asyncio
from typing import Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.browser.browser_manager import browser_manager


class MeetingState(str, Enum):
    """Current state of the meeting session."""
    IDLE = "idle"
    JOINING = "joining"
    AUTHENTICATING = "authenticating"
    IN_LOBBY = "in_lobby"
    IN_MEETING = "in_meeting"
    LEAVING = "leaving"
    LEFT = "left"
    ERROR = "error"


@dataclass
class MeetingSession:
    """Active meeting session info."""
    meeting_url: str
    state: MeetingState
    joined_at: Optional[datetime] = None
    error_message: Optional[str] = None


class GoogleMeetAutomation:
    """
    Automates Google Meet interactions.
    
    Capabilities:
    - Sign in to Google account
    - Join meetings via URL
    - Configure mic/camera before joining
    - Leave meetings gracefully
    """
    
    def __init__(self):
        self._page: Optional[Page] = None
        self._session: Optional[MeetingSession] = None
    
    @property
    def is_in_meeting(self) -> bool:
        """Check if currently in a meeting."""
        return (
            self._session is not None and 
            self._session.state == MeetingState.IN_MEETING
        )
    
    @property
    def current_session(self) -> Optional[MeetingSession]:
        """Get current meeting session info."""
        return self._session
    
    async def _ensure_browser(self) -> None:
        """Ensure browser is initialized."""
        if not browser_manager.is_initialized:
            await browser_manager.initialize()
    
    async def _get_or_create_page(self) -> Page:
        """Get existing page or create a new one."""
        if self._page is None or self._page.is_closed():
            self._page = await browser_manager.get_page()
        return self._page
    
    async def _is_signed_in(self, page: Page) -> bool:
        """Check if already signed in to Google."""
        try:
            # Navigate to Google account page
            await page.goto("https://accounts.google.com", wait_until="networkidle", timeout=15000)
            
            # If we see the profile picture or account name, we're signed in
            signed_in = await page.locator('[data-ogsr-up]').count() > 0
            if not signed_in:
                # Alternative check - look for sign out button
                signed_in = await page.locator('text=Sign out').count() > 0
            
            return signed_in
        except Exception:
            return False
    
    async def sign_in_to_google(self) -> bool:
        """
        Sign in to Google account.
        
        Returns:
            True if sign-in successful, False otherwise
        """
        await self._ensure_browser()
        page = await self._get_or_create_page()
        
        # Check if already signed in
        if await self._is_signed_in(page):
            print("Already signed in to Google")
            return True
        
        print("Signing in to Google...")
        
        try:
            # Go to Google sign-in
            await page.goto("https://accounts.google.com/signin", wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)
            
            # Enter email - try multiple selectors
            email_selectors = [
                'input[type="email"]',
                'input[name="identifier"]',
                '#identifierId',
                'input[aria-label*="email" i]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = page.locator(selector)
                    if await email_input.count() > 0:
                        await email_input.first.wait_for(timeout=5000, state="visible")
                        await email_input.first.fill(settings.google_account_email)
                        print(f"Email entered using selector: {selector}")
                        email_filled = True
                        break
                except Exception:
                    continue
            
            if not email_filled:
                raise Exception("Could not find email input field")
            
            # Click Next button
            next_selectors = [
                'button:has-text("Next")',
                '#identifierNext',
                'button[type="button"]'
            ]
            
            for selector in next_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        await button.first.click()
                        print(f"Clicked Next button")
                        break
                except Exception:
                    continue
            
            # Wait for password page to load
            await asyncio.sleep(3)
            
            # Enter password - try multiple selectors
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[name="Passwd"]',
                '#password input',
                'input[aria-label*="password" i]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = page.locator(selector)
                    count = await password_input.count()
                    if count > 0:
                        await password_input.first.wait_for(timeout=15000, state="visible")
                        await password_input.first.fill(settings.google_account_password)
                        print(f"Password entered using selector: {selector}")
                        password_filled = True
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not password_filled:
                # Take a screenshot for debugging
                await page.screenshot(path="password_page_debug.png")
                raise Exception("Could not find password input field. Screenshot saved.")
            
            # Click Next/Sign in button
            submit_selectors = [
                'button:has-text("Next")',
                '#passwordNext',
                'button[type="submit"]',
                'button:has-text("Sign in")'
            ]
            
            for selector in submit_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        await button.first.click()
                        print(f"Clicked submit button")
                        break
                except Exception:
                    continue
            
            # Wait for sign-in to complete
            await asyncio.sleep(5)
            
            # Verify sign-in success
            if await self._is_signed_in(page):
                print("Successfully signed in to Google")
                return True
            else:
                # Check for 2FA or other challenges
                print("Sign-in may require additional verification (2FA, CAPTCHA, etc.)")
                print("   Please complete verification in the browser window...")
                # Wait longer for manual intervention if needed
                await asyncio.sleep(45)
                return await self._is_signed_in(page)
            
        except Exception as e:
            print(f"Google sign-in failed: {e}")
            return False
    
    async def join_meeting(
        self,
        meeting_url: str,
        mic_enabled: bool = False,
        camera_enabled: bool = False
    ) -> MeetingSession:
        """
        Join a Google Meet meeting.
        
        Args:
            meeting_url: Full Google Meet URL
            mic_enabled: Whether to enable microphone
            camera_enabled: Whether to enable camera
        
        Returns:
            MeetingSession with current state
        """
        self._session = MeetingSession(
            meeting_url=meeting_url,
            state=MeetingState.JOINING
        )
        
        try:
            await self._ensure_browser()
            page = await self._get_or_create_page()
            
            # Navigate directly to the meeting (skip automated sign-in)
            # If user is not logged in, the browser will stay open for manual login
            print(f"Navigating to meeting: {meeting_url}")
            self._session.state = MeetingState.JOINING
            
            try:
                await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"Navigation timeout or error: {e}")
                # Continue anyway, page might have loaded
            
            # Wait for page to load
            await asyncio.sleep(5)
            
            # UNCONDITIONAL WAIT for manual login/verification
            print("Waiting 60 seconds for manual interaction...")
            print("   Please check the opened browser window!")
            print("   If you see a login page, SIGN IN NOW.")
            print("   If you see the meeting lobby, just wait.")
            
            for i in range(12):  # 60 seconds
                await asyncio.sleep(5)
                # Check if we are already in meeting or lobby to exit early
                if await self._check_in_meeting(page) or (await self._click_join_button(page)):
                    print("Detected meeting/join button early!")
                    break
                print(f"   Waiting... ({60 - (i+1)*5}s remaining)")
            
            # Check if we need to sign in
            # If we see a sign-in page, wait for manual login
            if await self._needs_signin(page):
                print("Please sign in to Google in the browser window...")
                print("   Waiting 60 seconds for manual login...")
                self._session.state = MeetingState.AUTHENTICATING
                
                # Wait for user to manually sign in
                for i in range(12):  # 12 * 5 = 60 seconds
                    await asyncio.sleep(5)
                    if not await self._needs_signin(page):
                        print("Sign-in detected!")
                        break
                    if i == 5:
                        print("   Still waiting... (30s remaining)")
                
                # Check if we're now on the meeting page
                current_url = page.url
                if "meet.google.com" not in current_url or "accounts.google.com" in current_url:
                    # Try navigating to meeting again
                    await page.goto(meeting_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(3)
            
            # Disable mic and camera before joining
            await self._configure_media(page, mic_enabled, camera_enabled)
            
            # Click "Join now" or "Ask to join" button
            join_clicked = await self._click_join_button(page)
            if not join_clicked:
                self._session.state = MeetingState.ERROR
                self._session.error_message = "Could not find join button"
                return self._session
            
            # Wait for join to complete
            await asyncio.sleep(3)
            
            # Check if we're in lobby or meeting
            is_in_meeting = await self._check_in_meeting(page)
            
            if is_in_meeting:
                self._session.state = MeetingState.IN_MEETING
                self._session.joined_at = datetime.now()
                print("Successfully joined the meeting!")
            else:
                # Might be in lobby
                self._session.state = MeetingState.IN_LOBBY
                print("Waiting in lobby for host approval...")
            
            return self._session
            
        except Exception as e:
            self._session.state = MeetingState.ERROR
            self._session.error_message = str(e)
            print(f"Failed to join meeting: {e}")
            import traceback
            traceback.print_exc()
            return self._session
    
    async def _needs_signin(self, page: Page) -> bool:
        """Check if we're on a Google sign-in page."""
        try:
            url = page.url
            if "accounts.google.com" in url:
                return True
            # Check for sign-in elements
            signin_indicators = [
                'input[type="email"]',
                'input[name="identifier"]',
                '#identifierId'
            ]
            for selector in signin_indicators:
                if await page.locator(selector).count() > 0:
                    return True
            return False
        except Exception:
            return False
    
    async def _configure_media(
        self,
        page: Page,
        mic_enabled: bool,
        camera_enabled: bool
    ) -> None:
        """Configure microphone and camera before joining."""
        try:
            # Try to find and click mic toggle (to mute)
            if not mic_enabled:
                mic_button = page.locator('[data-is-muted="false"][aria-label*="microphone" i]')
                if await mic_button.count() > 0:
                    await mic_button.first.click()
                    print("Microphone muted")
            
            # Try to find and click camera toggle (to disable)
            if not camera_enabled:
                camera_button = page.locator('[data-is-muted="false"][aria-label*="camera" i]')
                if await camera_button.count() > 0:
                    await camera_button.first.click()
                    print("Camera disabled")
                    
        except Exception as e:
            print(f"Could not configure media: {e}")
    
    async def _click_join_button(self, page: Page) -> bool:
        """Find and click the join button."""
        join_selectors = [
            'button:has-text("Join now")',
            'button:has-text("Ask to join")',
            'button:has-text("Join")',
            '[data-idom-class*="join"]',
            'button[jsname="Qx7uuf"]',  # Common join button
        ]
        
        for selector in join_selectors:
            try:
                button = page.locator(selector)
                if await button.count() > 0:
                    await button.first.click()
                    print(f"Clicked join button")
                    return True
            except Exception:
                continue
        
        return False
    
    async def _check_in_meeting(self, page: Page) -> bool:
        """Check if currently in the meeting room."""
        try:
            # Look for elements that indicate we're in the meeting
            in_meeting_indicators = [
                '[data-meeting-title]',
                '[data-self-name]',
                'button[aria-label*="Leave call"]',
                'button[aria-label*="Present now"]',
            ]
            
            for selector in in_meeting_indicators:
                if await page.locator(selector).count() > 0:
                    return True
            
            return False
        except Exception:
            return False
    
    async def leave_meeting(self) -> bool:
        """
        Leave the current meeting.
        
        Returns:
            True if successfully left, False otherwise
        """
        if not self._page or self._page.is_closed():
            return False
        
        if not self._session:
            return False
        
        self._session.state = MeetingState.LEAVING
        
        try:
            # Click leave button
            leave_selectors = [
                'button[aria-label*="Leave call"]',
                'button[aria-label*="Leave meeting"]',
                '[data-idom-class*="leave"]',
            ]
            
            for selector in leave_selectors:
                try:
                    button = self._page.locator(selector)
                    if await button.count() > 0:
                        await button.first.click()
                        print("👋 Left the meeting")
                        self._session.state = MeetingState.LEFT
                        return True
                except Exception:
                    continue
            
            # If no leave button found, just close the page
            await self._page.close()
            self._page = None
            self._session.state = MeetingState.LEFT
            print("👋 Closed meeting page")
            return True
            
        except Exception as e:
            print(f"❌ Error leaving meeting: {e}")
            self._session.state = MeetingState.ERROR
            self._session.error_message = str(e)
            return False
    
    async def shutdown(self) -> None:
        """Cleanup and shutdown."""
        if self._session and self._session.state == MeetingState.IN_MEETING:
            await self.leave_meeting()
        
        if self._page and not self._page.is_closed():
            await self._page.close()
        
        self._page = None
        self._session = None


# Singleton instance
google_meet = GoogleMeetAutomation()
