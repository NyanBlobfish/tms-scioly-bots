from discord.ext import commands
from typing import Literal
from utils.checks import is_staff


class BaseCogs(commands.Cog):
    """Core commands for unloading and reloading"""
    print('Base Cog Loaded')

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.check(is_staff())
    async def cogs(self, ctx):
        x = self.bot.cogs
        await ctx.send(f"```{x}```")

    @cogs.command()
    @commands.check(is_staff())
    async def load(self, ctx,
                   cog: Literal["cogs.mod", "cogs.listeners", "cogs.fun", "cogs.general", "cogs.tasks", "cogs.base"]):
        '''Loads a module'''
        try:
            self.bot.load_extension(cog)
            await ctx.send("Successfully loaded " + f"`{cog}`" + " module")
            print("loaded module: " + cog)
        except Exception as e:
            await ctx.send("Error with loading " + f"`{cog}`" + f"\n Error {e}")

    @cogs.command()
    @commands.check(is_staff())
    async def reload(self, ctx,
                     cog: Literal["cogs.mod", "cogs.listeners", "cogs.fun", "cogs.general", "cogs.tasks", "cogs.base"]):
        '''Reloads a module'''
        try:
            self.bot.reload_extension(cog)
            await ctx.send("Successfully reloaded " + f"`{cog}`" + " module")
            print("reloaded module: " + cog)
        except Exception as e:
            await ctx.send("Error with reloading " + f"`{cog}`" + f"\n Error {e}")

    @cogs.command()
    @commands.check(is_staff())
    async def unload(self, ctx,
                     cog: Literal["cogs.mod", "cogs.listeners", "cogs.fun", "cogs.general", "cogs.tasks", "cogs.base"]):
        '''Unloads a module'''
        try:
            self.bot.unload_extension(cog)
            await ctx.send("Successfully unloaded " + f"`{cog}`" + " module")
            print("unloaded module: " + cog)
        except Exception as e:
            await ctx.send("Error with unloading " + f"`{cog}`" + f"\n Error {e}")

    @cogs.command()
    async def removecog(self, ctx,
                        cog: Literal["cogs.mod", "cogs.listeners", "cogs.fun", "cogs.general", "cogs.tasks", "cogs.base"]):
        '''Removes a module'''
        try:
            self.bot.remove_cog(cog)
            await ctx.send("Successfully removed " + f"`{cog}`" + " module")
            print("removed module: " + cog)
        except Exception as e:
            await ctx.send("Error with removing " + f"`{cog}`" + f"\n Error {e}")

    @cogs.command()
    async def removelistener(self, ctx,
                             listener: Literal[
                             "on_member_join",
                             "on_message",
                             "on_message_edit",
                             "on_command_error",
                             "on_error",
                             "on_raw_message_delete",
                             "on_member_update",
                             "on_raw_reaction_add"]):
        '''Removes a listener'''
        try:
            self.bot.remove_listener(func = listener, name = listener)
            await ctx.send("Successfully removed listener " + f"`{listener}`" + " module")
            print("removed listener: " + listener)
        except Exception as e:
            await ctx.send("Error with removing " + f"`{listener}`" + f"\n Error {e}")

    @cogs.command()
    async def loadlistener(self, ctx,
                             listener: Literal[
                                 "on_member_join",
                                 "on_message",
                                 "on_message_edit",
                                 "on_command_error",
                                 "on_error",
                                 "on_raw_message_delete",
                                 "on_member_update",
                                 "on_raw_reaction_add"]):
        '''adds a listener'''
        try:
            self.bot.add_listener(func=listener, name=listener)
            await ctx.send("Successfully added listener " + f"`{listener}`" + " module")
            print("added listener: " + listener)
        except Exception as e:
            await ctx.send("Error with adding " + f"`{listener}`" + f"\n Error {e}")

    @cogs.command()
    async def removecommand(self, ctx,
                             command):
        '''Removes a command'''
        try:
            self.bot.remove_command(name=command)
            await ctx.send("Successfully removed command " + f"`{command}`" + " module")
            print("removed command: " + command)
        except Exception as e:
            await ctx.send("Error with removing " + f"`{command}`" + f"\n Error {e}")


def setup(bot):
    bot.add_cog(BaseCogs(bot))
