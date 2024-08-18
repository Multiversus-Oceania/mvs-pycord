import os
import discord
from dotenv import load_dotenv
from a_pythonversus import a_MvsAPI, a_User

load_dotenv()


class MvsPycord(discord.Bot):
    def __init__(self):
        super().__init__()
        self.mvs_api = None

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.initialize_api()
        await self.sync_commands()
        print('Bot is ready!')

    async def initialize_api(self):
        try:
            self.mvs_api = await a_MvsAPI.MvsAPIWrapper().__aenter__()
            print("API initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize API: {e}")
            self.mvs_api = None

    async def close(self):
        if self.mvs_api:
            await self.mvs_api.__aexit__(None, None, None)
        await super().close()


bot = MvsPycord()


@bot.slash_command(name="player_info", description="Get player information")
async def player_info(ctx, username: str):
    await ctx.defer()  # Defer the response
    if bot.mvs_api is None:
        await ctx.followup.send("Sorry, the API is not available at the moment.")
        return

    try:
        user = await a_User.User.from_username(bot.mvs_api, username)
        await ctx.followup.send(f"Player info for {username}: {user.user_summary()}")
    except Exception as e:
        await ctx.followup.send(f"An error occurred while fetching player info: {str(e)}")


@bot.slash_command(name="sync", description="Manually sync bot commands")
@discord.default_permissions(administrator=True)
async def sync(ctx):
    await ctx.defer()  # Defer the response
    await bot.sync_commands()
    await ctx.followup.send("Commands synced!")


async def main():
    async with bot:
        await bot.start(os.getenv('BOT_TOKEN'))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
