"""
Browser Manager

Manages Playwright browser lifecycle with persistent context support.
"""

import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from app.config import settings


class BrowserManager:
    """
    Manages Playwright browser instances with persistent context.
    
    Features:
    - Persistent login sessions (no need to re-authenticate)
    - Configurable headless/headed mode
    - Screenshot and video recording support
    """
    
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize Playwright and launch browser."""
        if self._is_initialized:
            return
        
        # Ensure browser data directory exists
        data_dir = Path(settings.browser_data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Start Playwright
        print("Starting Playwright...")
        try:
            self._playwright = await async_playwright().start()
            print("Playwright started")
            
            # Launch browser with persistent context
            # This keeps login sessions between runs
            print(f"Launching Chromium (headless={settings.browser_headless})...")
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(data_dir.absolute()),
                headless=settings.browser_headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--start-maximized",
                ],
                ignore_default_args=["--enable-automation"],
                viewport=None, # Use maximized window
                locale="en-US",
                permissions=["microphone", "camera"],
            )
            print("Browser context created successfully")
        except Exception as e:
            print(f"Browser launch failed: {e}")
            import traceback
            traceback.print_exc()
            raise e
        
        self._is_initialized = True
        print("🌐 Browser initialized successfully")
    
    async def get_page(self) -> Page:
        """Get a new page in the browser context."""
        if not self._is_initialized:
            await self.initialize()
        
        print("📄 Creating new page...")
        page = await self._context.new_page()
        print("✅ New page created")
        
        # Add anti-detection scripts
        await page.add_init_script("""
            // Override webdriver detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override chrome automation detection
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return page
    
    async def close_page(self, page: Page) -> None:
        """Close a specific page."""
        if page and not page.is_closed():
            await page.close()
    
    async def shutdown(self) -> None:
        """Shutdown the browser and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        self._is_initialized = False
        print("Browser shutdown complete")
    
    @property
    def is_initialized(self) -> bool:
        """Check if browser is initialized."""
        return self._is_initialized
    
    @asynccontextmanager
    async def page_context(self):
        """Context manager for page lifecycle."""
        page = await self.get_page()
        try:
            yield page
        finally:
            await self.close_page(page)


# Singleton instance
browser_manager = BrowserManager()
