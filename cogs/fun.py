import asyncio
import datetime
import random
import unicodedata

import discord

import math
import io
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException as UnsupportedLanguage
from discord.commands.commands import Option, option, slash_command
from discord.ext import commands

from utils.autocomplete import GOOGLE_LANGUAGES, image_filters
from utils.checks import is_not_blacklisted
from utils.doggo import get_akita, get_cotondetulear, get_doggo, get_shiba
from utils.variables import *
from utils.views import Counter, TicTacToe


class Fun(commands.Cog):
    """Commands for Fun!"""

    print('FunCommands Cog Loaded')

    def __init__(self, bot):
        self.bot = bot

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f973')

    async def cog_check(self, ctx):
        return await is_not_blacklisted(ctx)

    @slash_command(guild_ids=[SERVER_ID])
    async def roll(self, ctx):
        '''Rolls a dice'''
        await ctx.defer()
        await asyncio.sleep(2)
        sayings = ['<:dice1:884113954383728730>',
                   '<:dice2:884113968493391932>',
                   '<:dice3:884113979033665556>',
                   '<:dice4:884113988596674631>',
                   '<:dice5:884114002156867635>',
                   '<:dice6:884114012281901056>'
                   ]
        response = sayings[math.floor(random.random() * len(sayings))]
        await ctx.respond(f"{response}")

    @slash_command(guild_ids=[SERVER_ID])
    async def magic8ball(self, ctx, question: str):
        '''Swishes a Magic8ball'''
        await ctx.defer()
        await asyncio.sleep(3)
        sayings = [
            "Yes.",
            "Ask again later.",
            "Not looking good.",
            "Cannot predict now.",
            "It is certain.",
            "Try again.",
            "Without a doubt.",
            "Don't rely on it.",
            "Outlook good.",
            "My reply is no.",
            "Don't count on it.",
            "Yes - definitely.",
            "Signs point to yes.",
            "I believe so.",
            "Nope.",
            "Concentrate and ask later.",
            "Try asking again.",
            "For sure not.",
            "Definitely no."
        ]
        response = random.choice(sayings)
        await ctx.respond(f"**{response}**")

    @slash_command(guild_ids=[SERVER_ID])
    async def candy(self, ctx):
        '''Feeds panda some candy!'''
        global fish_now
        r = random.random()

        if len(str(fish_now)) > 1500:
            fish_now = round(pow(fish_now, 0.5))
            if fish_now == 69: fish_now = 70
            return await ctx.respond(
                "Woah! Panda's amount of candy is a little too much, so it unfortunately has to be square rooted.")
        if r > 0.9:
            fish_now += 100
        if fish_now == 1  
        return await ctx.respond(f"You feed panda one candy. Panda now has {fish_now} piece of candy!")
                
            if fish_now == 69: fish_now = 70
            return await ctx.respond(
                f"Wow, you gave panda a super candy! Added 100 candy! Panda now has {fish_now} pieces of candy!")
        if r > 0.1:
            fish_now += 1
            if fish_now == 69:
                fish_now = 70
                return await ctx.respond(f"You feed panda two candy. Panda now has {fish_now} pieces of candy!")
            else:
                return await ctx.respond(f"You feed panda one candy. Panda now has {fish_now} pieces of candy!")
        if r > 0.02:
            fish_now += 0
            return await ctx.respond(
                f"You can't find any candy... and thus can't feed panda. Panda still has {fish_now} pieces of candy.")

    @slash_command(guild_ids=[SERVER_ID])
    async def stealcandy(self, ctx):
        '''Steals some candy from panda'''
        global fish_now
        member = ctx.author
        r = random.random()
        if member.id in STEALFISH_BAN:
            return await ctx.respond("Hey! You've been banned from stealing candy for now.")
        if r >= 0.75:
            ratio = r - 0.5
            fish_now = round(fish_now * (1 - ratio))
            per = round(ratio * 100)
            return await ctx.respond(f"You stole {per}% of panda's candy!")
        if r >= 0.416:
            date = datetime.datetime.now() + datetime.timedelta(hours=1)
            STEALFISH_BAN.append(member.id)
            CRON_LIST.append({
                'type': "UNSTEALCANDYBAN",
                'user': member.id,
                'time': date,
                'tag': str(member)
            })
            return await ctx.respond(
                f"Sorry {member.mention}, but it looks like you're going to be banned from using this command for 1 "
                f"hour!")
        if r >= 0.25:
            date = datetime.datetime.now() + datetime.timedelta(days=1)
            STEALFISH_BAN.append(member.id)
            CRON_LIST.append({
                'type': "UNSTEALCANDYBAN",
                'user': member.id,
                'time': date,
                'tag': str(member)
            })
            return await ctx.respond(
                f"Sorry {member.mention}, but it looks like you're going to be banned from using this command for 1 day!")
        if r >= 0.01:
            return await ctx.respond("Hmm, nothing happened. *crickets*")
        else:
            STEALFISH_BAN.append(member.id)
            return await ctx.respond(
                "You are banned from using `!stealcandy` until the next version of TMS-Bot is released.")

    @slash_command(guild_ids=[SERVER_ID])
    async def count(self, ctx):
        '''Counts the number of members in the server'''
        guild = ctx.author.guild
        await ctx.respond(f"Currently, there are `{len(guild.members)}` members in the server.")

    @slash_command(guild_ids=[SERVER_ID])
    async def latex(self, ctx, latex: Option(str, description="LaTex Code")):
        '''Displays an image of an equation, uses LaTex as input'''
        print(latex)
        new_args = latex.replace(" ", r"&space;")
        print(new_args)
        await ctx.respond(r"https://latex.codecogs.com/png.latex?\dpi{175}{\color{White}" + new_args + "}")

    @slash_command(guild_ids=[SERVER_ID])
    @option(name="manipulate", autocomplete=discord.utils.basic_autocomplete(values=image_filters))
    async def image(self, ctx: discord.ApplicationContext, member: discord.User, manipulate):
        params = {
            'image_url': member.avatar.url,
        }

        await ctx.defer()
        r = await self.bot.session.get(f'https://api.jeyy.xyz/image/{manipulate}', params=params)
        buf = io.BytesIO(await r.read())

        await ctx.respond(file=discord.File(buf, 'image.gif'))

    @slash_command(guild_ids=[SERVER_ID])
    async def profile(self,
                      ctx,
                      user: discord.User
                      ):

        if user is None:
            avatar = ctx.author.avatar
            await ctx.respond(f'{avatar}')
        else:
            try:
                await ctx.respond(f'{user.avatar}')
            except Exception as e:
                await ctx.respond(f"Couldn't find profile: {e}")

    @slash_command(guild_ids=[SERVER_ID])
    async def grade(self,
                    ctx,
                    a: Option(float, description="Your points"),
                    b: Option(float, description="Total points")
                    ):
        '''Returns a percentage/grade'''
        x = a / b
        z = x * 100
        if z < 60:
            await ctx.respond(f'{round(z, 2)}% F')
        elif 60 <= z < 70:
            await ctx.respond(f'{round(z, 2)}% D')
        elif 70 <= z < 80:
            await ctx.respond(f'{round(z, 2)}% C')
        elif 80 <= z < 90:
            await ctx.respond(f'{round(z, 2)}% B')
        elif 90 <= z < 93:
            await ctx.respond(f'{round(z, 2)}% A-')
        elif 93 <= z < 97:
            await ctx.respond(f'{round(z, 2)}% A')
        elif 97 <= z <= 100:
            await ctx.respond(f'{round(z, 2)}% A+')
        elif z > 100:
            await ctx.respond(f"{round(z, 2)}% A++ must've gotten extra credit")

    @slash_command(guild_ids=[SERVER_ID])
    async def ping(self, ctx):
        '''Get the bot's latency'''
        latency = round(self.bot.latency * 1000, 2)
        em = discord.Embed(title="Pong :ping_pong:",
                           description=f":clock1: My ping is {latency} ms!",
                           color=0x16F22C)
        await ctx.respond(embed=em)

    @slash_command(guild_ids=[SERVER_ID])
    async def counter(self, ctx):
        """Starts a counter for pressing."""
        await ctx.respond('Press!', view=Counter())

    @slash_command(guild_ids=[SERVER_ID])
    async def tictactoe(self, ctx):
        """Starts a tic-tac-toe game."""
        await ctx.respond('Tic Tac Toe: X goes first', view=TicTacToe())

    @slash_command(guild_ids=[SERVER_ID])
    async def shiba(self, ctx,
                    member: Option(discord.Member, description="Who are you trying to shiba?")):
        '''Shiba-s another user'''
        if member is None:
            return await ctx.respond("Tell me who you want to shiba!! :dog:")
        else:
            doggo = await get_shiba()
            await ctx.respond(doggo)
            await ctx.channel.send(f"{member.mention}, <@{ctx.author.id}> shiba-d you!!")

    @slash_command(guild_ids=[SERVER_ID])
    async def cottondetulear(self, ctx,
                             member: Option(discord.Member, description="Who are you trying to cottondetulear?")):
        '''"Cottondetulear-s Another Member!"'''
        if member is None:
            return await ctx.respond("Tell me who you want to cottondetulear!! :dog:")
        else:
            doggo = await get_cotondetulear()
            await ctx.respond(doggo)
            await ctx.channel.send(f"{member.mention}, {ctx.author.mention} cottondetulear-d you!!")

    @slash_command(guild_ids=[SERVER_ID])
    async def akita(self, ctx,
                    member: Option(discord.Member, description="Who are you trying to akita?")
                    ):
        """Akita-s a user!"""
        if member is None:
            return await ctx.respond("Tell me who you want to akita!! :dog:")
        else:
            doggo = await get_akita()
            await ctx.respond(doggo)
            await ctx.channel.send(f"{member.mention}, <@{ctx.author.id}> akita-d you!!")

    @slash_command(guild_ids=[SERVER_ID])
    async def doge(self, ctx,
                   member: Option(discord.Member, description="Who are you trying to doge?")):
        """Dogeee-s someone!"""
        if member is None:
            return await ctx.respond("Tell me who you want to dogeeee!! :dog:")
        else:
            doggo = await get_doggo()
            await ctx.respond(doggo)
            await ctx.channel.send(f"{member.mention}, <@{ctx.author.id}> dogeee-d you!!")

    @slash_command(guild_ids=[SERVER_ID])
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.
        Only up to 25 characters at a time.
        """

        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>'

        msg = '\n'.join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.respond('Output too long to display.')
        await ctx.respond(msg)

    #
    # async def to_emoji(self, emoji) -> discord.PartialEmoji:
    #     return emoji
    #
    # @slash_command(guild_ids=[SERVER_ID])
    # async def emoji(self, ctx, emoji: Any):
    #     """
    #     Makes an emoji bigger and shows it's formatting
    #     """
    #     if type(emoji) is not [discord.Emoji, discord.Emoji]:
    #         return await ctx.respond("Input must be a custom emoji")
    #     if emoji.animated:
    #         emoticon = f"*`<`*`a:{emoji.name}:{emoji.id}>`"
    #     else:
    #         emoticon = f"*`<`*`:{emoji.name}:{emoji.id}>`"
    #     embed = discord.Embed(description=f"{emoticon}", color=ctx.me.color)
    #     embed.set_image(url=emoji.url)
    #     await ctx.respond(embed=embed)

    @slash_command(guild_ids=[SERVER_ID])
    @option("language", autocomplete=discord.utils.basic_autocomplete(values=GOOGLE_LANGUAGES))
    async def translate(self, ctx, language: str, *, input: str):
        try:
            translator = GoogleTranslator(source='auto', target=language.lower())
            translated = translator.translate(input)
        except UnsupportedLanguage:
            return await ctx.respond(
                embed=discord.Embed(title='Error Occured', description='Please input valid language to translate to'))
        embed = discord.Embed()
        embed.add_field(name=f'Text in `{language}:`', value=translated)
        embed.set_footer(text='Please remember, that the translations can\'t be a 100% accurate')

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
