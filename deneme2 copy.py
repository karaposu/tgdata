from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData("config.ini")
    
    # Fetch messages using numeric ID
    messages = await tg.get_messages(
        group_id=1707717812,  # Numeric ID exactly as shown by list_groups()
        limit=10,
        with_progress=True
    )
    
   
    
    # Export to CSV
    tg.export_messages(messages, "2026messages.csv")

asyncio.run(main())