import asyncio 
from bot import main
from handlers import admin, users

if __name__ == "__main__":
    # Running the main function asynchronously using asyncio
    asyncio.run(main())
