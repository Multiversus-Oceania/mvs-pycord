import os
import discord
from dotenv import load_dotenv
from a_pythonversus import a_MvsAPI, a_User
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

class MyBot(discord.Bot):
    def __init__(self):
        super().__init__()
        self.mvs_api = None
        self.sync_on_ready = True

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.bg_task = self.loop.create_task(self.background_task())
        logger.info('------')

    async def background_task(self):
        await self.initialize_api()
        if self.sync_on_ready:
            await self.sync_commands_with_retry()

    async def initialize_api(self):
        try:
            logger.info("Initializing MvsAPIWrapper...")
            self.mvs_api = await a_MvsAPI.MvsAPIWrapper().__aenter__()
            logger.info("MvsAPIWrapper initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize MvsAPIWrapper: {e}")
            self.mvs_api = None

    async def sync_commands_with_retry(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                logger.info(f"Syncing commands (attempt {attempt + 1})...")
                await self.sync_commands(force=True)
                logger.info("Commands synced successfully!")
                return
            except Exception as e:
                logger.error(f"Error syncing commands: {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    logger.error("Max retries reached. Please sync manually using the /sync command.")

    async def close(self):
        if self.mvs_api:
            await self.mvs_api.__aexit__(None, None, None)
        await super().close()

bot = MyBot()

@bot.slash_command(name="player_info", description="Get player information")
async def player_info(ctx, username: str):
    await ctx.defer()
    if bot.mvs_api is None:
        logger.error("MvsAPIWrapper is not initialized.")
        await ctx.respond("Sorry, the API is not available at the moment. Please try again later.")
        return

    try:
        logger.info(f"Fetching player info for username: {username}")
        user = await a_User.User.from_username(bot.mvs_api, username)
        logger.info(f"Successfully fetched player info for {username}")
        await ctx.respond(f"Player info for {username}: {user.user_summary()}")
    except AttributeError as e:
        logger.error(f"AttributeError in player_info: {e}")
        await ctx.respond("An error occurred while fetching player info. The API might not be fully initialized.")
    except Exception as e:
        logger.error(f"Error in player_info: {e}")
        await ctx.respond(f"An error occurred while fetching player info: {str(e)}")

@bot.slash_command(name="sync", description="Manually sync bot commands")
@discord.default_permissions(administrator=True)
async def sync(ctx):
    await ctx.defer()
    await bot.sync_commands_with_retry()
    await ctx.respond("Command sync process completed. Check console for details.")

@bot.slash_command(name="initialize_api", description="Manually initialize the API")
@discord.default_permissions(administrator=True)
async def initialize_api_command(ctx):
    await ctx.defer()
    await bot.initialize_api()
    if bot.mvs_api:
        await ctx.respond("API initialized successfully.")
    else:
        await ctx.respond("Failed to initialize API. Check console for details.")

async def main():
    async with bot:
        await bot.start(os.getenv('BOT_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())