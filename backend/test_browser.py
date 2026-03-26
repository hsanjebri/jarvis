"""
Test script to debug browser join issues
"""
import asyncio
from app.browser.google_meet import google_meet

async def test_join():
    try:
        print("🧪 Testing Google Meet join...")
        
        # Test meeting URL
        test_url = "https://meet.google.com/yqu-opgx-xzd"
        
        session = await google_meet.join_meeting(
            meeting_url=test_url,
            mic_enabled=False,
            camera_enabled=False
        )
        
        print(f"✅ Session state: {session.state}")
        print(f"   Error: {session.error_message}")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Leave
        await google_meet.leave_meeting()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_join())
