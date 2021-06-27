import discord
from discord.ext import commands
import os
import platform
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
from utils import get_expire_time
from discord import FFmpegPCMAudio, PCMVolumeTransformer, Colour
from discord.ext.commands import Bot, Context, check, Cooldown, CooldownMapping, BucketType, Command, CommandError, \
    CommandOnCooldown
import pafy
import re
from typing import Union, Optional
from discord import User, DMChannel, Message, Embed, Colour, Activity, ActivityType
from discord.utils import get
import urllib
import asyncio
import time
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}




TOKEN = ""

version = '1.0.0'
intents = discord.Intents.default()
intents.members = True
intents.presences = True
game = discord.Game(f"Kodluyoruz Pomodoro Bot  ||  {version} || !yardim")
bot = commands.Bot(command_prefix='!', status=discord.Status.online,
                   activity=game, help_command=None, intents=intents)

mode : str = "working"
sched = AsyncIOScheduler()

client = discord.Client()

@bot.event
async def on_ready():
    print(" ---------------------")
    print(" POMODORO BOT BAŞLATILDI")
    print(" ---------------------")
    sched.start()


@bot.command(name='yardim')
async def yardim(ctx: Context):
    help_embed = Embed(title="Kodluyoruz Pomodoro Botu", description="Pomodoro komut menüsü", color=0xff7e00)
    help_embed.set_thumbnail(url="https://cdn.discordapp.com/app-icons/858045409599815711/3d7f822ff866b571a96ee5620cf8f22a.png?size=128")
    help_embed.add_field(name="!baslat [ÇALIŞMA SÜRESİ]", value="Pomodoro Sayacını girdiğiniz çalışma süresine göre başlatır")
    help_embed.add_field(name="!durdur", value="Hali Hazırda çalışan pomodoro sayacını durdurur")
    help_embed.add_field(name="!durum", value="Molada mı olduğunuzu çalışma modunda mı olduğunuzu öğrenebilirsiniz")
    help_embed.add_field(name="!sarkiyi_oynat [ŞARKI_İSMİ]", value="Girdiğiniz şarkıyı youtubedan bulur ve ses kanalında çalar. Maalesef şuanda playlist özelliği desteklememektedir.")
    help_embed.add_field(name="!sarkiyi_duraklat", value="Şarkıyı duraklatabilir sonrasında devam ettirebilirsiniz.")
    help_embed.add_field(name="!sarki_devamet", value="Duraklatılan şarkıyı devam ettirir.")
    help_embed.add_field(name="!sarkiyi_durdur", value="Çalan şarkıyı tamamen durdurur.")
    help_embed.add_field(name="!todo ya da !todo l/?/liste/list", value="Hazırladığınız yapılacaklar listesini görüntülemenizi sağlar.")
    help_embed.add_field(name="!todo a/+/ekle/add [GÖREV_İSMİ]", value="Yeni görev tanımı yapmanızı sağlar.")
    help_embed.add_field(name="!todo r/-/kaldir/remove [GÖREV_İSMİ]", value="Tanımlanmış bir görevi kaldırmanızı sağlar.")

    await ctx.send(embed=help_embed)



""" Müzik oynatma durdurma işlemleri


===================================================
 """
@bot.command(name="sarkiyi_oynat")
async def play_music(ctx, *args):

        print(args)
        search = " ".join(args).encode('utf-8').strip()
        print(search)
        if ctx.message.author.voice == None:
            await ctx.send(embed=discord.Embeds.txt("Ses Kanalı Yok", "Bu komutu kullanmak için ses kanalında olmalısınız!", ctx.author))
            return

        channel = ctx.message.author.voice.channel

        voice = discord.utils.get(ctx.guild.voice_channels, name=channel.name)

        voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)

        if voice_client == None:
            voice_client = await voice.connect()
        else:
            await voice_client.move_to(channel)

        search = str(search).replace(" ", "+")

        html = urllib.request.urlopen(" https://www.youtube.com/results?search_query=" + search)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

        await ctx.send("Şuan Oynatılıyor: https://www.youtube.com/watch?v=" + video_ids[0])

        song = pafy.new(video_ids[0])  # creates a new pafy object

        audio = song.getbestaudio()  # gets an audio source

        source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)  # converts the youtube audio source into a source discord can use
        print(audio.url)
        voice_client.play(source)  # play the source

@bot.command(name="sarkiyi_duraklat")
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client                
    voice_channel.pause()
    
@bot.command(name="sarki_devamet")
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client                
    voice_channel.resume()

@bot.command(name="sarkiyi_durdur")
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client                
    voice_channel.stop()

""" 

        Pomodoro Bölümü işlemleri

======================================

"""
@bot.command(name='baslat')
async def start_pomodoro_timer(ctx, work_time: int):

    if len(sched.get_jobs()) > 0:
        await ctx.channel.send(
            f"```css\n[⚠️ Kronometre hali hazırda çalışıyor!]\n - Durdurma komutu: !durdur```")
        return

    async def break_schedule(work_time, break_time):
        await ctx.channel.send(
            f"{ctx.author.mention}```css\n[🔥 Mola Bitti!] Hadi çalışmaya başlayalım :)```")
        mode = "breaking"
        work_expire_time = get_expire_time(work_time)
        
        sched.add_job(work_schedule, 'date', run_date=work_expire_time, id=0, args=[
                      work_time, 5], misfire_grace_time=300)
        
        pass

    async def work_schedule(work_time, break_time):
        await ctx.channel.send(
            f"{ctx.author.mention}```css\n[🏁 Çalışma Zamanı bitti!] Hadi biraz dinlenelim :)```")
        mode = "working"
        break_expire_time = get_expire_time(break_time)
        sched.add_job(break_schedule, 'date', id=0,run_date=break_expire_time,
                      args=[work_time, 5], misfire_grace_time=300)
        pass

    work_expire_time = get_expire_time(work_time)
    sched.add_job(work_schedule, 'date', run_date=work_expire_time,
                  args=[work_time, 5], misfire_grace_time=300)

    await ctx.channel.send(
        f"```css\n[ {work_time} dakika çalış, {5} dakika dinlen] Zamanlayıcı Başladı. Kolay gelsin!.\n - durdurma komutu : !durdur```")

@bot.command(name='durum')
async def status(ctx: Context):
    if mode == "working":
        await ctx.send(f"{ctx.author.mention}```css\nŞuan çalışma modundasınız. Sayacı durdurmak için: !durdur```")
    elif mode == "breaking":
        await ctx.send(f"{ctx.author.mention}```css\nŞuan moladasınız. Sayacı durdurmak için: !durdur```")
    else:
        print("Durum belirlenemedi.")
        print(mode)
@bot.command(name='durdur')
async def stop_pomodoro_timer(ctx):
    
    sched.remove_all_jobs()
    await ctx.channel.send(
        f"```css\n Pomodoro Zamanlayıcısı durduruldu.\n - başlatma komutu : !başlat [ÇALIŞMA SÜRESİ] [MOLA SÜRESİ]```")




""" 
        Yapılacaklar Listesi Kodları 

==============================================
"""

class SharedCooldown(Cooldown):
    def __init__(self, rate, per, type):
        super().__init__(rate, per, type)

    def copy(self):
        return self


class SharedCooldownMapping(CooldownMapping):
    def __init__(self, original):
        super().__init__(original)

    def copy(self):
        return self

    @property
    def cooldwon(self):
        return self._cooldown

    @classmethod
    def from_cooldown(cls, rate, per, type):
        return cls(SharedCooldown(rate, per, type))


def shared_cooldown(rate, per, type=BucketType.default):
    cooldown = SharedCooldown(rate, per, type)
    cooldown_mapping = SharedCooldownMapping(cooldown)

    def decorator(func):
        if isinstance(func, Command):
            func._buckets = cooldown_mapping
        else:
            func.__commands_cooldown__ = cooldown
        return func

    return decorator


class TodoEmbed(Embed):
    def __init__(self, **kwargs):
        super().__init__(title=':white_check_mark: Yapılacaklar Listesi **', colour=Colour.from_rgb(119, 178, 85), **kwargs)
        self.set_footer(text=FOOTER)

    @staticmethod
    def from_embed(origin: Embed):
        return TodoEmbed(description=origin.description)

    def set_author_(self, user: User):
        self.title += str(user) + '**'
        self.set_thumbnail(url=user.avatar_url)

FOOTER = '!todo I Love Python 💜 - Mustafa Berat Kurt'
NOTHING_TO_DO = 'Şuanda eklenmiş yapılacak görev yok. Bu komutla ekleme yapabilirsin *`!todo [GOREV ADI]`*!'
TODO_MAX_LENGTH = 128
todo_cooldown = shared_cooldown(1, 1, type=BucketType.user)
def add_todo(embed: Embed, content: str):
    todos = [r'\* ' + content]
    if embed.description:
        todos.extend(embed.description.split('\n'))
    embed.description = '\n'.join([r'\* ' + line[3:] for line in todos])


def remove_todo(embed: TodoEmbed, key: str) -> str:
    todos = list(reversed(embed.description.split('\n')))
    removed = r'\*  '
    for i, line in enumerate(todos):
        if key in line:
            removed = todos.pop(i)
            break
    if removed[3:]:
        embed.description = '\n'.join([r'\* ' + line[3:] for line in reversed(todos)])
    return removed[3:]


def get_todo_embed(message: Message):
    if message is None:
        return TodoEmbed()
    for e in message.embeds:
        if e.footer and e.footer.text == FOOTER:
            return TodoEmbed.from_embed(e)
    return TodoEmbed()


async def get_message(user: User):
    channel: DMChannel = user.dm_channel
    if channel is None:
        channel = await user.create_dm()
    message = await channel.history().find(
        lambda m: m.author == bot.user and get_todo_embed(m) is not None)
    if message is None:
        message = await channel.history().find(lambda m: m.author == bot.user)
    return message


def tokens_len(count: tuple or int):
    if type(count) != tuple:
        count = (count,)

    def predicate(ctx: Context) -> bool:
        return len(ctx.message.content.split()) in count

    return check(predicate)


async def update_todo(todo_embed: TodoEmbed, ctx: Context,
                      content: str = None, delete_after: Optional[Union[int, float]] = 60):
    data_message = await get_message(ctx.author)
    todo_embed.set_author_(ctx.author)
    tasks = list()
    if todo_embed.description:
        if ctx.guild is None:
            tasks.append(ctx.send(embed=todo_embed))
            if data_message is not None:
                tasks.append(data_message.delete())
        else:
            tasks.append(ctx.send(content=content, embed=todo_embed, delete_after=delete_after))
            if data_message is None:
                tasks.append(ctx.author.send(content, embed=todo_embed))
            else:
                tasks.append(data_message.edit(embed=todo_embed))
    elif ctx.guild is None:
        tasks.append(ctx.send(NOTHING_TO_DO))
        if data_message is not None:
            tasks.append(data_message.delete())
    else:
        tasks.append(ctx.send(NOTHING_TO_DO, delete_after=delete_after))
        if data_message is not None:
            tasks.append(data_message.delete())
    await asyncio.wait(tasks)


@bot.group(name='todo', aliases=('yapilacaklar', ), invoke_without_command=True)
@todo_cooldown
async def todo(ctx: Context, *, content: str = ''):
    if content:
        await todo_add(ctx, content=content)
    else:
        await todo_list(ctx)


@todo.command(name='+', aliases=('add', 'a', 'ekle'))
@todo_cooldown
async def todo_add(ctx: Context, *, content: str):
    if len(content) > TODO_MAX_LENGTH:
        await ctx.send(f'İçerik çok uzun!!! İçeriğiniz şundan daha kısa olmalıdır: {TODO_MAX_LENGTH} ')
        return
    data_message = await get_message(ctx.author)
    todo_embed = get_todo_embed(data_message)
    add_todo(todo_embed, content)
    if len(todo_embed.description) > 2048:
        await ctx.send('Senin yapılacaklar listen şuan dolu... yeni bir tane eklemek için bir todo gürevini kaldırabilirsin!')
        return
    await update_todo(todo_embed, ctx, f' `{content}` senin yapılacaklar listene eklendi!')


@todo.command(name='?', aliases=('list', 'l', 'liste'))
@tokens_len(2)
@todo_cooldown
async def todo_list(ctx: Context):
    data_message = await get_message(ctx.author)
    await update_todo(get_todo_embed(data_message), ctx, delete_after=None)


@todo.command(name='-', aliases=('remove', 'r', 'kaldir'))
@todo_cooldown
async def todo_remove(ctx: Context, *, key: str):
    data_message = await get_message(ctx.author)
    todo_embed = get_todo_embed(data_message)
    removed = remove_todo(todo_embed, key)
    if removed:
        await update_todo(todo_embed, ctx, f'`{removed}` Görevi yapılacaklar listesinden kaldırıldı')
    else:
        await ctx.send(f'task about `{key}` is not found.')



""" 
    Diğer Bölümler 
=========================
"""

# @bot.command(name="emegi_gecenler")
# async def creds(ctx: Context):
#     embed = Embed(title="Berat Kurt", description="Bu Bot Berat Kurt tarafından Kodluyoruz Jr. Discord sunucusu için kodlanmıştır.")
#     embed.add_field(name="Kodluyoruz Web Sitesi", value="https://www.kodluyoruz.org/")
#     embed.add_field(name="Github", value="https://github.com/zekkontro")
#     embed.add_field(name="Instagram", value="https://www.instagram.com/brtwlf/")
    
#     await ctx.send(embed=embed)

"Botu Çalıştır"
bot.run(TOKEN)
