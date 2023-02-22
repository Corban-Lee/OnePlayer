import discord
from discord.ext import commands

class ExceptionHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        print(error)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction, error):
        command = interaction.app_command
        ctx = interaction.context

        await ctx.send(f"An error occurred while executing the {command} command: {error}")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(ExceptionHandler(bot))