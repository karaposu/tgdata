from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
    tg = TgData("config.ini")
    
    # Fetch messages using numeric ID, and download each message's media (photos/
    # videos) into a folder during the fetch. The saved file path for each message
    # lands in the MediaPath column, so the CSV references the files on disk.
    messages = await tg.get_messages(
        group_id=1707717812,  # Numeric ID exactly as shown by list_groups()
        limit=50,
        with_progress=True,
        download_media_to="media_here",  # media files saved here; paths -> MediaPath column
    )
    
   
    
    # Export to CSV — includes MediaType / MediaPath / MessageLink columns, so each
    # row points to its downloaded file in 2026_media/ (raw bytes aren't written to CSV).
    tg.export_messages(messages, "2026messages.csv")

    n_media = messages['MediaPath'].notna().sum()
    print(f"Saved {len(messages)} messages to 2026messages.csv; "
          f"{n_media} media files downloaded to 2026_media/")

    await tg.close()

asyncio.run(main())