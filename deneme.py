
from tgdata import TgData
import asyncio

async def main():
    # Initialize the client
     
    tg = TgData( "/Users/ns/Desktop/projects/telegram-group-scraper/config.ini")
    # tg = TgData("config.ini")
    
    # List available groups and channels
    groups = await tg.list_groups()

    print(groups)

if __name__ == "__main__":
    asyncio.run(main())


#  1707717812                 Анталья продажа недвижимость жильё  ...        True              1539
#   1215923105         Анталья аренда недвижимость жильё квартиры  ...        True              7609
#   1642458915                               Недвижимость Анталия  ...        True              9778