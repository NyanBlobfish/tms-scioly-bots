from discord.ext import tasks, commands
import discord
from utils.variables import *
import datetime
from typing import Union


class CronTasks(commands.Cog):
    """Cron Tasks"""
    print('Tasks Cog Loaded')

    def __init__(self, bot):
        self.bot = bot
        self.cron.start()

    @tasks.loop(minutes=1)
    async def cron(self):
        print("Executed cron.")
        cron_list: list[dict[str, Union[datetime.datetime, Union[str, discord.User.id]]]] = CRON_LIST

        for task in cron_list:
            if datetime.datetime.now() > task['time']:
                try:
                    if task['type'] == "UNBAN":
                        server = self.bot.get_guild(SERVER_ID)
                        member = await self.bot.fetch_user(task['user'])
                        await server.unban(member)
                        CRON_LIST.remove(task)
                        print(f"Unbanned user ID: {member.id}")

                    elif task['type'] == "UNMUTE":
                        server = self.bot.get_guild(SERVER_ID)
                        member = server.get_member(task['user'])
                        role = discord.utils.get(server.roles, name=ROLE_MUTED)
                        self_role = discord.utils.get(server.roles, name=ROLE_SELFMUTE)
                        await member.remove_roles(role, self_role)
                        CRON_LIST.remove(task)
                        print(f"Unmuted user ID: {member.id}")

                    elif task['type'] == "UNSTEALCANDYBAN":
                        STEALFISH_BAN.remove(task['user'])
                        CRON_LIST.remove(task)
                        print(f"Un-stealcandybanneded user ID: {task['user']}")

                    else:
                        print("ERROR:")
                        reporter_cog = self.bot.get_cog('Reporter')
                        await reporter_cog.create_cron_task_report(task)
                except Exception:
                    reporter_cog = self.bot.get_cog('Reporter')
                    await reporter_cog.create_cron_task_report(task)

    @staticmethod
    async def add_to_cron(item_dict: dict):
        """
        Adds the given document to the CRON list.
        """
        CRON_LIST.append(item_dict)
        print(f"Added item: {item_dict} to CRON_LIST")

    async def schedule_unban(self, user: discord.User, time: datetime.datetime):
        item_dict = {
            'type': "UNBAN",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)

    async def schedule_unmute(self, user: discord.User, time: datetime.datetime):
        item_dict = {
            'type': "UNMUTE",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)

    async def schedule_unselfmute(self, user: discord.User, time: datetime.datetime):
        item_dict = {
            'type': "UNSELFMUTE",
            'user': user.id,
            'time': time,
            'tag': str(user)
        }
        await self.add_to_cron(item_dict)


def setup(bot):
    bot.add_cog(CronTasks(bot))
