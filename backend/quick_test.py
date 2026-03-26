"""Quick test to see browser error"""
import asyncio
import sys
sys.path.insert(0, 'c:/Users/hassa/.gemini/antigravity/scratch/jarvis/backend')

from app.browser.google_meet import google_meet

async def test():
    print("Testing browser launch...")
    try:
        session = await google_meet.join_meeting(
            meeting_url="https://meet.google.com/test-test-test",
            mic_enabled=False,
            camera_enabled=False
        )
        print(f"State: {session.state}")
        print(f"Error: {session.error_message}")
        await asyncio.sleep(10)
        await google_meet.leave_meeting()
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
