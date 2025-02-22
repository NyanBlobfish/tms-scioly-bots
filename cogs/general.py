import asyncio
import datetime
import os
from collections import Counter
from fractions import Fraction
from math import sqrt
from typing import Optional

import discord
import pkg_resources
import psutil
from discord.commands.commands import Option, slash_command
from discord.ext import commands

from cogs.github import Github
from utils import times
from utils.checks import is_not_blacklisted
from utils.rules import RULES
from utils.variables import *
from utils.views import ReportView


class General(commands.Cog):
    """General commands."""

    print('GeneralCommands Cog Loaded')

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.bot.launch_time = datetime.datetime.utcnow()

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f62f')

    async def cog_check(self, ctx) -> bool:
        return await is_not_blacklisted(ctx)

    def cog_unload(self) -> None:
        pass

    def get_bot_uptime(self) -> str:
        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime = f"{days} Days, {hours} Hours, {minutes} Minutes, {seconds} Seconds"
        return uptime

    @staticmethod
    async def _basic_cleanup_strategy(ctx, search):
        count = 0
        async for msg in ctx.history(limit=search, before=ctx.message):
            if msg.author == ctx.me and not (msg.mentions or msg.role_mentions):
                await msg.delete()
                count += 1
        return {'Bot': count}

    @staticmethod
    async def _complex_cleanup_strategy(ctx, search):

        def check(m):
            return m.author == ctx.me or m.content.startswith("!" or "?")

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @staticmethod
    async def _regular_user_cleanup_strategy(ctx, search):
        def check(m):
            return (m.author == ctx.me or m.content.startswith("!" or "?")) and not (m.mentions or m.role_mentions)

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @staticmethod
    def format_commit(commit):
        short, _, _ = commit.message.partition('\n')
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(commit_tz)

        # [`hash`](url) message (offset)
        offset = times.format_relative(commit_time.astimezone(datetime.timezone.utc))
        return f'[`{short_sha2}`](https://github.com/pandabear189/tms-scioly-bots/commit/{commit.hex}) {short} ({offset})'

    @slash_command(guild_ids=[SERVER_ID])
    async def rule(
            self,
            ctx,
            number: Option(str,
                           description="Which rule to display",
                           choices=["1", "2", "3", "4", "5", "6"])
    ):
        """Gets a specified rule."""
        rule = RULES[int(number) - 1]
        embed = discord.Embed(title="",
                              description=f"**Rule {number}:**\n> {rule}",
                              color=0xff008c)
        await ctx.respond(embed=embed)

    @slash_command(guild_ids=[SERVER_ID])
    async def report(self, ctx, reason):
        """Creates a report that is sent to staff members."""
        server = self.bot.get_guild(SERVER_ID)
        reports_channel = discord.utils.get(server.text_channels, id=CHANNEL_REPORTS)
        ava = ctx.author.avatar
        if ava is None:
            ava = ""

        message = reason
        embed = discord.Embed(title="Report received", description=" ", color=0xFF0000)
        embed.add_field(name="User:", value=f"{ctx.author.mention} \n id: `{ctx.author.id}`")
        embed.add_field(name="Report:", value=f"`{message}`")
        embed.set_author(name=f"{ctx.author}", icon_url=ava)
        await reports_channel.send(embed=embed, view=ReportView())
        await ctx.respond("Thanks, report created.")

    @staticmethod
    def tick(opt, label=None):
        lookup = {
            True: '<:greenTick:899466945672392704>',
            False: '<:redTick:899466976748003398>',
            None: '<:greyTick:899466890102075393>',
        }
        emoji = lookup.get(opt, '<:redTick:330090723011592193>')
        if label is not None:
            return f'{emoji}: {label}'
        return emoji

    @slash_command(guild_ids=[SERVER_ID])
    async def serverinfo(self, ctx, *, guild_id: int = None):
        """Shows info about the current server."""

        if guild_id is not None and await self.bot.is_owner(ctx.author):
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return await ctx.respond(f'Invalid Guild ID given.')
        else:
            guild = ctx.guild

        roles = [role.name.replace('@', '@\u200b') for role in guild.roles]

        if not guild.chunked:
            async with ctx.typing():
                await guild.chunk(cache=True)

        # figure out what channels are 'secret'
        everyone = guild.default_role
        everyone_perms = everyone.permissions.value
        secret = Counter()
        totals = Counter()
        for channel in guild.channels:
            allow, deny = channel.overwrites_for(everyone).pair()
            perms = discord.Permissions((everyone_perms & ~deny.value) | allow.value)
            channel_type = type(channel)
            totals[channel_type] += 1
            if not perms.read_messages:
                secret[channel_type] += 1
            elif isinstance(channel, discord.VoiceChannel) and (not perms.connect or not perms.speak):
                secret[channel_type] += 1

        e = discord.Embed()
        e.title = guild.name
        e.description = f'**ID**: {guild.id}\n**Owner**: {guild.owner}'
        if guild.icon:
            e.set_thumbnail(url=guild.icon.url)

        channel_info = []
        key_to_emoji = {
            discord.TextChannel: '<:text_channel:899326950785576970>',
            discord.VoiceChannel: '<:voice_channel:899326987255021619>',
        }
        for key, total in totals.items():
            secrets = secret[key]
            try:
                emoji = key_to_emoji[key]
            except KeyError:
                continue

            if secrets:
                channel_info.append(f'{emoji} {total} ({secrets} locked)')
            else:
                channel_info.append(f'{emoji} {total}')

        info = []
        features = set(guild.features)
        all_features = {
            'PARTNERED': 'Partnered',
            'VERIFIED': 'Verified',
            'DISCOVERABLE': 'Server Discovery',
            'COMMUNITY': 'Community Server',
            'FEATURABLE': 'Featured',
            'WELCOME_SCREEN_ENABLED': 'Welcome Screen',
            'INVITE_SPLASH': 'Invite Splash',
            'VIP_REGIONS': 'VIP Voice Servers',
            'VANITY_URL': 'Vanity Invite',
            'COMMERCE': 'Commerce',
            'LURKABLE': 'Lurkable',
            'NEWS': 'News Channels',
            'ANIMATED_ICON': 'Animated Icon',
            'BANNER': 'Banner',
        }

        for feature, label in all_features.items():
            if feature in features:
                info.append(f'{self.tick(True)}: {label}')

        if info:
            e.add_field(name='Features', value='\n'.join(info))

        e.add_field(name='Channels', value='\n'.join(channel_info))

        if guild.premium_tier != 0:
            boosts = f'Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts'
            last_boost = max(guild.members, key=lambda m: m.premium_since or guild.created_at)
            if last_boost.premium_since is not None:
                boosts = f'{boosts}\nLast Boost: {last_boost} ({times.format_relative(last_boost.premium_since)})'
            e.add_field(name='Boosts', value=boosts, inline=False)

        bots = sum(m.bot for m in guild.members)
        fmt = f'Total: {guild.member_count} ({bots} bots)'

        e.add_field(name='Members', value=fmt, inline=False)
        e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 10 else f'{len(roles)} roles')

        emoji_stats = Counter()
        for emoji in guild.emojis:
            if emoji.animated:
                emoji_stats['animated'] += 1
                emoji_stats['animated_disabled'] += not emoji.available
            else:
                emoji_stats['regular'] += 1
                emoji_stats['disabled'] += not emoji.available

        fmt = (
            f'Regular: {emoji_stats["regular"]}/{guild.emoji_limit}\n'
            f'Animated: {emoji_stats["animated"]}/{guild.emoji_limit}\n'
        )
        if emoji_stats['disabled'] or emoji_stats['animated_disabled']:
            fmt = f'{fmt}Disabled: {emoji_stats["disabled"]} regular, {emoji_stats["animated_disabled"]} animated\n'

        fmt = f'{fmt}Total Emoji: {len(guild.emojis)}/{guild.emoji_limit * 2}'
        e.add_field(name='Emoji', value=fmt, inline=False)
        e.set_footer(text='Created').timestamp = guild.created_at
        await ctx.respond(embed=e)

    @staticmethod
    async def say_permissions(ctx, member, channel):
        permissions = channel.permissions_for(member)
        e = discord.Embed(colour=member.colour)
        avatar = member.display_avatar.with_static_format('png')
        e.set_author(name=str(member), url=avatar)
        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace('_', ' ').replace('guild', 'server').title()
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        e.add_field(name='Allowed', value='\n'.join(allowed))
        e.add_field(name='Denied', value='\n'.join(denied))
        await ctx.respond(embed=e)

    @slash_command(guild_ids=[SERVER_ID])
    async def permissions(self, ctx,
                          member: Optional[discord.Member],
                          channel: Optional[discord.TextChannel]):
        """Shows a member's permissions in a specific channel.
        If no channel is given then it uses the current one.
        You cannot use this in private messages. If no member is given then
        the info returned will be yours.
        """
        channel = channel or ctx.channel
        if member is None:
            member = ctx.author

        await self.say_permissions(ctx, member, channel)

    @slash_command(guild_ids=[SERVER_ID])
    async def debugpermissions(self, ctx, guild_id: int, channel_id: int, author_id: int = None):
        """Shows permission resolution for a channel and an optional author."""

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.respond('Guild not found?')

        channel = guild.get_channel(channel_id)
        if channel is None:
            return await ctx.respond('Channel not found?')

        if author_id is None:
            member = guild.me
        else:
            member = await ctx.guild.get_member(author_id)

        if member is None:
            return await ctx.respond('Member not found?')

        await self.say_permissions(ctx, member, channel)

    @slash_command(guild_ids=[SERVER_ID])
    async def info(self, ctx, user: discord.User):
        """Shows info about a user."""

        user = user or ctx.author
        e = discord.Embed()
        roles = [role.name.replace('@', '@\u200b') for role in getattr(user, 'roles', [])]
        e.set_author(name=str(user))

        def format_date(dt):
            if dt is None:
                return 'N/A'
            return f'{times.format_dt(dt, "F")} ({times.format_relative(dt)})'

        e.add_field(name='ID', value=user.id, inline=False)
        e.add_field(name='Joined', value=format_date(getattr(user, 'joined_at', None)), inline=False)
        e.add_field(name='Created', value=format_date(user.created_at), inline=False)

        voice = getattr(user, 'voice', None)
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = f'{vc.name} with {other_people} others' if other_people else f'{vc.name} by themselves'
            e.add_field(name='Voice', value=voice, inline=False)

        if roles:
            e.add_field(name='Roles', value=', '.join(roles) if len(roles) < 15 else f'{len(roles)} roles',
                        inline=False)

        colour = user.colour
        if colour.value:
            e.colour = colour

        e.set_thumbnail(url=user.display_avatar.url)

        if isinstance(user, discord.User):
            e.set_footer(text='This member is not in this server.')

        await ctx.respond(embed=e)

    @slash_command(guild_ids=[SERVER_ID])
    async def tag(self,
                  ctx,
                  tag: Option(str, description="Name of the tag")
                  ):
        '''Retrieves a tag'''
        tag = tag.lower()
        if tag == 'rules':
            em1 = discord.Embed(title="Rules", description="Here are the rules for the 2021-22 season", color=0xff008c)
            em1.add_field(name='Division B Rules',
                          value="[Click Here](https://www.soinc.org/sites/default/files/2021-09/Science_Olympiad_Div_B_2022_Rules_Manual_Web_0.pdf/ \"Division B\")")
            em1.add_field(name='Division C Rules',
                          value="[Click Here](https://www.soinc.org/sites/default/files/2021-09/Science_Olympiad_Div_C_2022_Rules_Manual_Web_1.pdf/ \"Division C\")")
            await ctx.respond(embed=em1)

        elif tag == 'anatomy':
            em2 = discord.Embed(title="Anatomy & Physiology Rules",
                                description="Participants will be assessed on their understanding of the anatomy and physiology for the human Nervous, Sense Organs, and Endocrine systems.  \n This Event may be administered as a written test or as series of lab-practical stations which can include but are not limited to experiments, scientific apparatus, models, illustrations, specimens, data collection and analysis, and problems for students to solve.",
                                color=0xff008c)
            em2.add_field(name='Full Anatomy Rules',
                          value="[Click Here](https://www.soinc.org/sites/default/files/2021-09/Science_Olympiad_Div_B_2022_Rules_Manual_Web_0.pdf#page=7/ \"Anatomy\")")
            await ctx.respond(embed=em2)

        elif tag == 'bpl':
            em3 = discord.Embed(title="Bio Process Lab Rules", color=0xff008c)
            em3.add_field(name='Full Bio Process Lab',
                          value="[Click Here](https://www.soinc.org/sites/default/files/2021-09/Science_Olympiad_Div_B_2022_Rules_Manual_Web_0.pdf#page=9/ \"Bio Process Lab\")")
            await ctx.respond(embed=em3)

        else:
            await ctx.respond("Sorry I couldn't find that tag", mention_author=False)

    @slash_command(guild_ids=[SERVER_ID])
    async def invite(self, ctx):
        '''Gives you a 1 time use invite link'''
        x = await ctx.channel.create_invite(max_uses=1)
        await ctx.respond(x)

    _bot = discord.SlashCommandGroup(
        "bot",
        "Commands related to the bot itself",
        [SERVER_ID]
    )

    @_bot.command(name="permissions")
    async def _permissions(self, ctx, channel: Optional[discord.TextChannel]):
        """Shows the bot's permissions in a specific channel.
        If no channel is given then it uses the current one.
        This is a good way of checking if the bot has the permissions needed
        to execute the commands it wants to execute.
        To execute this command you must have Manage Roles permission.
        You cannot use this in private messages.
        """
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @_bot.command()
    async def uptime(self, ctx):
        '''Sends how long the bot has been online'''
        uptime = self.get_bot_uptime()
        await ctx.respond(f"**{uptime}**")

    @_bot.command()
    async def about(self, ctx):
        """Tells you information about the bot itself."""

        revision = Github.get_last_commits(self, count=5)
        embed = discord.Embed(description='Latest Changes:\n' + revision)
        # embed = discord.Embed(description='Latest Changes:\n')
        embed.colour = discord.Colour.blurple()

        # To properly cache myself, I need to use the bot support server.
        support_guild = self.bot.get_guild(816806329925894217)
        owner = await support_guild.fetch_member(747126643587416174)
        name = str(owner)
        embed.set_author(name=name, icon_url=owner.display_avatar.url, url='https://github.com/pandabear189')

        # statistics
        total_members = 0
        total_unique = len(self.bot.users)

        text = 0
        voice = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            if guild.unavailable:
                continue

            total_members += guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        embed.add_field(name='Members', value=f'{total_members} total\n{total_unique} unique')
        embed.add_field(name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')

        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')

        dpyversion = pkg_resources.get_distribution('py-cord').version
        embed.add_field(name='Guilds', value=guilds)
        embed.add_field(name='Number of Commands', value=(len(self.bot.commands) + len(self.bot.application_commands)))
        uptime = self.get_bot_uptime()
        embed.add_field(name="Uptime", value=uptime)
        embed.set_footer(text=f'Made with discord.py v{dpyversion}', icon_url='https://i.imgur.com/RPrw70n.png')
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed)

    @_bot.command(name="health")
    async def _health(self, ctx):
        """Various bot health monitoring tools."""

        # This uses a lot of private methods because there is no
        # clean way of doing this otherwise.

        HEALTHY = discord.Colour.brand_green()
        UNHEALTHY = discord.Colour.brand_red()

        total_warnings = 0

        embed = discord.Embed(title='Bot Health Report', colour=HEALTHY)

        description = [
        ]

        task_retriever = asyncio.all_tasks
        all_tasks = task_retriever(loop=self.bot.loop)

        event_tasks = [
            t for t in all_tasks
            if 'Client._run_event' in repr(t) and not t.done()
        ]

        cogs_directory = os.path.dirname(__file__)
        tasks_directory = os.path.join('discord', 'ext', 'tasks', '__init__.py')
        inner_tasks = [
            t for t in all_tasks
            if cogs_directory in repr(t) or tasks_directory in repr(t)
        ]

        bad_inner_tasks = ", ".join(hex(id(t)) for t in inner_tasks if t.done() and t._exception is not None)
        total_warnings += bool(bad_inner_tasks)
        embed.add_field(name='Inner Tasks', value=f'Total: {len(inner_tasks)}\nFailed: {bad_inner_tasks or "None"}')
        embed.add_field(name='Events Waiting', value=f'Total: {len(event_tasks)}', inline=False)

        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name='Process', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU', inline=False)

        ws_rate_limit = self.bot.is_ws_ratelimited()
        description.append(f'Websocket Rate Limit: {ws_rate_limit}')

        global_rate_limit = self.bot.http._global_over.set()
        description.append(f'Global Rate Limit: {global_rate_limit}')

        if ws_rate_limit or total_warnings >= 3 or len(event_tasks) >= 4:
            embed.colour = UNHEALTHY

        embed.set_footer(text=f'{total_warnings} warning(s)')
        embed.description = '\n'.join(description)
        await ctx.respond(embed=embed)

    @slash_command(guild_ids=[SERVER_ID])
    async def suggest(self, ctx, suggestion):
        '''Make a suggestion for the server, team or bot'''
        server = self.bot.get_guild(SERVER_ID)
        suggest_channel = discord.utils.get(server.text_channels, id=CHANNEL_SUGGESTIONS)
        reports_channel = discord.utils.get(server.text_channels, id=CHANNEL_REPORTS)
        embed = discord.Embed(title="New Suggestion", description=f"{suggestion}", color=discord.Color.blurple())
        embed.timestamp = discord.utils.utcnow()
        name = ctx.author.nick or ctx.author
        embed.set_author(name=name, icon_url=ctx.author.avatar)
        suggest_message = await suggest_channel.send(embed=embed)
        await suggest_message.add_reaction("\U0001f44d")
        await suggest_message.add_reaction("\U0001f44e")
        await reports_channel.send(embed=embed)
        suggest_url = suggest_message.jump_url
        embed2 = discord.Embed(title=" ", description=f"Posted! [Your Suggestion!]({suggest_url})")
        await ctx.respond(embed=embed2)
        suggest_id = suggest_message.id
        suggest_embed = suggest_message.embeds[0]
        copy_of_embed = suggest_embed.copy()
        copy_of_embed.add_field(name="Suggestion ID", value=f"`{suggest_id}`")
        await suggest_message.edit(embed=copy_of_embed)

    @slash_command(guild_ids=[SERVER_ID])
    async def cleanup(self, ctx, search: int = 100):
        """Cleans up the bot's messages from the channel.
        If a search number is specified, it searches that many messages to delete.
        If the bot has Manage Messages permissions then it will try to delete
        messages that look like they invoked the bot as well.
        After the cleanup is completed, the bot will send you a message with
        which people got their messages deleted and their count. This is useful
        to see which users are spammers.
        Members with Manage Messages can search up to 1000 messages.
        Members without can search up to 25 messages.
        """

        strategy = self._basic_cleanup_strategy
        is_mod = ctx.channel.permissions_for(ctx.author).manage_messages
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            if is_mod:
                strategy = self._complex_cleanup_strategy
            else:
                strategy = self._regular_user_cleanup_strategy

        if is_mod:
            search = min(max(2, search), 1000)
        else:
            search = min(max(2, search), 10)

        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'- **{author}**: {count}' for author, count in spammers)

        await ctx.respond('\n'.join(messages))

    @slash_command(guild_ids=[SERVER_ID])
    async def newusers(self, ctx, count: int = None):
        """Tells you the newest members of the server.
        This is useful to check if any suspicious members have
        joined.
        The count parameter can only be up to 25.
        """

        if not ctx.guild.chunked:
            members = await ctx.guild.chunk(cache=True)
        else:
            members = sorted(ctx.guild.members, key=lambda m: m.joined_at, reverse=True)[:count]

        e = discord.Embed(title='New Members', colour=discord.Colour.green())

        for member in members:
            body = f'Joined {times.format_relative(member.joined_at)}\nCreated {times.format_relative(member.created_at)}'
            e.add_field(name=f'{member} (ID: {member.id})', value=body, inline=False)

        await ctx.respond(embed=e)


class Math(commands.Cog):
    """Math commands"""

    print('Math Cog Loaded')

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0000270f')

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await is_not_blacklisted(ctx)

    def perfect_square(self, limit):
        accumulation_list = [1]
        index, increment = 0, 3
        while accumulation_list[-1] + increment <= limit:
            accumulation_list.append(accumulation_list[index] + increment)
            index += 1
            increment = 2 * index + 3
        return accumulation_list

    @slash_command(guild_ids=[SERVER_ID])
    async def quadratic(self, ctx,
                        a: Option(int, description=" `a` value in standard form: ax^2 + bx + c"),
                        b: Option(int, description=' `b` value in standard form: ax^2 + bx + c'),
                        c: Option(int, description=' `c` value in standard form: ax^2 + bx + c')
                        ):
        '''
        Solves a Quadratic Function
        `a:` represents the lead coefficient, if there is no coefficient; input 1
        `b:` the middle term coefficient
        `c:` the last term
        `ax^2 + bx + c`
        '''
        if a <= 0:
            return await ctx.respond('Lead coefficient of `0 or less` is **not** a quadratic!!')

        w = 4 * a * c
        square_root_value = b ** 2 - w
        bottom = 2 * a

        if square_root_value < 0:
            if square_root_value < 0:
                square_root_value = square_root_value * -1
                if sqrt(square_root_value).is_integer():
                    print(int(sqrt(square_root_value)))
                    print("is perfect square (imaginary/complex)")
                    p = int(-b + sqrt(square_root_value))
                    q = int(-b - sqrt(square_root_value))

                    if (p / bottom).is_integer():
                        if (q / bottom).is_integer():
                            if q == p:
                                return await ctx.respond(
                                    r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x=" + f"{int(p / bottom)}i" + r"}")
                            else:
                                return await ctx.respond(
                                    r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(p / bottom)}i" + r"\;\;" + f"x_2={int(q / bottom)}i" + r"}")
                        else:
                            return await ctx.respond(
                                r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(p / bottom)}" + r"\;\;" + r"x_2=\frac{" + f"{q}" + r"}{" + f"{bottom}" + r"}}")
                    if (q / bottom).is_integer():
                        k, l = (p / bottom).as_integer_ratio()
                        x = Fraction(k, l).limit_denominator()
                        k, l = x.as_integer_ratio()
                        return await ctx.respond(
                            r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(q / bottom)}i" + r"\;\;" + r"x_2=\frac{" + f"{k}i" + r"}{" + f"{l}" + r"}}")

                    # Find perfect squares that are factors of n
                factors = [square for square in self.perfect_square(square_root_value / 2) if
                           square_root_value % square == 0 and square > 1]
                if len(factors) == 0:
                    print('\u221A', square_root_value)
                    i = "i"
                    return await ctx.respond(
                        r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + r"x=\frac{" + f"{-b}" + rf"\pm\," + fr"{i}" + r"\sqrt" + f"{square_root_value}" + r"}{" + f"{bottom}" + r"}" + "}")
                else:
                    x = int(sqrt(max(factors)))  # Coefficient
                    y = int(square_root_value / max(factors))  # Argument of the square root
                    return await ctx.respond(
                        r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + r"x=\frac{" + f"{-b}" + rf"\pm{x}i\sqrt" + f"{y}" + r"}{" + f"{bottom}" + r"}" + "}")

        if sqrt(square_root_value).is_integer():
            print(int(sqrt(square_root_value)))
            print("is perfect square")
            p = int(-b + sqrt(square_root_value))
            q = int(-b - sqrt(square_root_value))

            if (p / bottom).is_integer():
                if (q / bottom).is_integer():
                    if q == p:
                        return await ctx.respond(
                            r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x=" + f"{int(p / bottom)}" + r"}")
                    else:
                        return await ctx.respond(
                            r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(p / bottom)}" + r"\;\;" + f"x_2={int(q / bottom)}" + r"}")
                else:
                    return await ctx.respond(
                        r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(p / bottom)}" + r"\;\;" + r"x_2=\frac{" + f"{q}" + r"}{" + f"{bottom}" + r"}}")
            if (q / bottom).is_integer():
                k, l = (p / bottom).as_integer_ratio()
                x = Fraction(k, l).limit_denominator()
                k, l = x.as_integer_ratio()
                return await ctx.respond(
                    r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}x_1=" + f"{int(q / bottom)}" + r"\;\;" + r"x_2=\frac{" + f"{k}" + r"}{" + f"{l}" + r"}}")
            else:
                # TODO figure out what the hell to do here
                latex = r"\frac{" + f"{-b}" + r"\pm" + f"{int(sqrt(square_root_value))}" + r"}{" + f"{int(2 * a)}" + r"}"
                return await ctx.respond(
                    r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + latex + "}")

            # Find perfect squares that are factors of n
        factors = [square for square in self.perfect_square(square_root_value / 2) if
                   square_root_value % square == 0 and square > 1]
        if len(factors) == 0:
            print('\u221A', square_root_value)
            return await ctx.respond(
                r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + r"x=\frac{" + f"{-b}" + rf"\pm\sqrt" + f"{square_root_value}" + r"}{" + f"{bottom}" + r"}" + "}")
        else:
            x = int(sqrt(max(factors)))  # Coefficient
            y = int(square_root_value / max(factors))  # Argument of the square root
            return await ctx.respond(
                r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + r"x=\frac{" + f"{-b}" + rf"\pm{x}\sqrt" + f"{y}" + r"}{" + f"{bottom}" + r"}" + "}")


def setup(bot):
    bot.add_cog(General(bot))
    bot.add_cog(Math(bot))
