#!/usr/bin/env python3

import asyncio, random, time, re, os, sys, json, shutil, subprocess, stat
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import discord
import youtube_dl
import requests

from discord import FFmpegPCMAudio
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime
from itertools import cycle
from google_images_download import google_images_download
from PIL import Image, ImageDraw, ImageFont
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

# command prefix, bot initialization and removal of default 'help' command
prefix = '!'
bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')

status = cycle(['Status 1', 'Status 2', 'Status 3']) # status cycle

muted = {} # list of muted people

vote = False # votemute active or not
votes = {'yes':0, 'no':0} # vote tally
voters = [] # list of voters

u_vote = False # voteunmute active or not
u_votes = {'yes':0, 'no':0} # vote tally
u_voters = [] # list of voters


@bot.event
async def on_ready(): # runs upon bot being initialized
    status_loop.start() # start status_loop
    auto_unmute.start() # start auto_unmute loop
    muted_list_export.start() # start muted_list_export loop
    print(f'{bot.user.name}#{bot.user.discriminator} is online')
    print(f'discord.py version: {discord.__version__}')


@bot.event
async def on_member_join(member): # runs when a new member joins the server
    if member in muted: # checks if member is in the muted list
        role = discord.utils.get(member.guild.roles, name='muted by the people') # gets the role name
        await  member.add_roles(role) # assigns the role
    else:
        pass # TO-DO: add a default 'member' role to all users upon joining


@bot.event
async def on_message(message): # runs on a new message being sent in the server
    global votes
    global voters
    global u_votes
    global u_voters
    
    message_content = message.content # store message content in a variable
    author = message.author # grab the author name from the message
    if author == bot.user: # make sure the message was not sent by the bot
        return

    if vote: # check if votemute is active
        if (message_content == 'yes') and not(author in voters): # check if someone typed 'yes'
            votes['yes'] = votes['yes'] + 1 # add 1 to votes counter
            voters.append(author) # add author to voters list
            print(f'{author} voted yes')

        elif (message_content == 'no') and not(author in voters): # check if someone typed 'no'
            votes['no'] = votes['no'] + 1 # add 1 to the no counter
            voters.append(author) # add author to voters list
            print(f'{author} voted no')

    elif u_vote: # check if voteunmute is active
        if (message_content == 'yes') and not(author in u_voters):
            u_votes['yes'] = u_votes['yes'] + 1
            u_voters.append(author)
            print(f'{author} voted yes')

        elif (message_content == 'no') and not(author in u_voters):
            u_votes['no'] = u_votes['no'] + 1
            u_voters.append(author)
            print(f'{author} voted no')
    
    else:
        pass # TO-DO: To be decided

    # log all messages sent in the server with a time stamp in the format YYYY:MM:DD HH:MM:SS  
    dir = 'cache\log.txt' 
    with open(dir, 'a') as f:
       time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       f.write(f"<{time_stamp}>{message_content}\n")

    await bot.process_commands(message) # tells bot to process the custom commands below


@tasks.loop(seconds=10) 
async def status_loop(): # changes the bot's status every 10 seconds
    await bot.change_presence(activity=discord.Game(next(status)))


@tasks.loop(seconds=10) # work in progress
async def muted_list_export(): # exports the list of muted users every 10 seconds
    muted_json = json.dumps(muted) # this function needs work, is not finished yet.
    dir = 'muted.json'
    with open(dir, 'w+') as f:
        json.dump(muted_json, f)


@tasks.loop(seconds=10) # work in progress
async def muted_list_import(): # imports the list of muted users every 10 seconds
    #global
    #dir = 'muted.json'
    #with open(dir, 'w+') as f:
        #muted = json.load(f)
    pass


@tasks.loop(seconds=10) # TO-DO
async def auto_unmute(): # auto unmutes people and updates the muted 
    for member in muted:
        if time.time() - muted[member] >= 900:
            role = discord.utils.get(member.guild.roles, name='muted by the people')
            await  member.remove_roles(role)
            print(f'auto_unmuted: unmuted {member}')
            del muted[member]

# function to log commands
def logger(func, ctx, start):
    """
    func (Type: string): function name
    start (Type: boolean): start or end of function
    ctx (Type: object): Discord.context 
    """
    time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if start == True:
        print(f'{time_stamp} - Command: {func} | Author: {ctx.message.author}')
    else:
        print(f'{time_stamp} - Task Finished Succesfully')


# used to add text to images
def text_wrap(text, font, max_width):
    """
    text (Type: string): text to be added to the image
    font (Type: object): Image.Font 
    max_width (Type: int): image width 
    """
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text) 
    else:
        # split the line by spaces to get words
        words = text.split(' ')  
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ''         
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:                
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word, 
            # add the line to the lines array
            lines.append(line)    
    return lines


# checks if a user is an administrator
def is_admin(user): 
    return user.guild_permissions.administrator


# calls git commands from terminal
def git(*args):
    return subprocess.check_call(['git'] + list(args))


@commands.command()
async def update(ctx):
    logger('update',ctx,True)

    if is_admin(ctx.message.author): 
        await ctx.send('updating the bot')
        if os.path.exists('bot.py'): # remove the old source file 
            os.remove('bot.py')
        if os.path.exists('turkey_bot'): # remove old cloned directory
            shutil.rmtree('turkey_bot')
        git('clone', 'https://github.com/h4sohail/turkey_bot.git') # Clones repo
        if os.path.exists('turkey_bot/bot.py'): # move file to working directory
            os.replace('turkey_bot/bot.py', '../turkey_bot/bot.py')
            # set execute permissions
            st = os.stat('bot.py') 
            os.chmod('bot.py', st.st_mode | stat.S_IEXEC)
        if os.path.exists('turkey_bot'): # cleanup
            shutil.rmtree('turkey_bot')
    else:
        await ctx.send('You are not authorized to use this command.')
    
    logger('update',ctx,False)


@commands.command()
async def reset(ctx):
    logger('reset',ctx,True)
    
    if is_admin(ctx.message.author):
        await ctx.send('clearing the cache')
        if os.path.exists('word_cloud.png'): # delete the last word cloud
            os.remove('word_cloud.png')
        if os.path.exists('downloads'): # delete cached google images
            shutil.rmtree('downloads')
        if os.path.exists('source.m4a'): # delete the last youtube sound file 
            os.remove('source.m4a')
        await ctx.send('cache cleared')
        await ctx.send('restarting the bot')
        os.execv('turkey_bot/bot.py', sys.argv) # restart the bot
    else:
        await ctx.send('you are not authorized to use this command :rage:')

    logger('reset',ctx,False)


@commands.command()
async def votemute(ctx, member:discord.Member=None):
    logger('votemute',ctx,True)
    
    global vote
    global votes
    global voters
    global muted
    guild = ctx.guild # get guild(server) information
    if vote or u_vote: # make sure only 1 voting session is active at a time
        await ctx.send('a vote is already in progress, please wait')
        return
        
    vote = True 

    await ctx.send(f'vote to mute started by {ctx.message.author}')
    await ctx.send('reply with [yes] or [no] to vote')

    await ctx.send('waiting 60 seconds for votes')
    await asyncio.sleep(30)
    
    await ctx.send('waiting 30 seconds for votes')
    await asyncio.sleep(20)

    await ctx.send('waiting 10 seconds for votes')
    await asyncio.sleep(10)

    yes_votes = votes['yes'] # get amount of yes votes
    no_votes = votes['no'] # get amount of no votes

    if yes_votes > no_votes: # compare results
        await ctx.send('the majority has voted yes, user will be muted for 15 minutes')
        
        role = discord.utils.get(member.guild.roles, name='muted by the people') # get the muted role
        await  member.add_roles(role) # assign the muted role
        muted[member] = time.time() # add member to the muted list with a time stamp
        print(f'{member} has been muted for 15 minutes')
        for invite in await guild.invites(): # remove muted users invites
            if invite.inviter == member:
                await invite.delete()
            else:
                pass
    if no_votes >= yes_votes:
        await ctx.send('the majority voted no, user will not be muted') 

    vote = False
    votes = {'yes':0, 'no':0}
   
    logger('votemute',ctx,False)


@commands.command()
async def voteunmute(ctx, member:discord.Member=None):
    logger('voteunmute',ctx,True)

    global u_vote
    global u_votes
    global u_voters

    if vote or u_vote:
        await ctx.send('a vote is already in progress, please wait')
        return

    u_vote = True

    await ctx.send(f'vote to mute started by {ctx.message.author}')
    await ctx.send('reply with [yes] or [no] to vote')

    await ctx.send('waiting 60 seconds for votes')
    await asyncio.sleep(30)
    
    await ctx.send('waiting 30 seconds for votes')
    await asyncio.sleep(20)

    await ctx.send('waiting 10 seconds for votes')
    await asyncio.sleep(10)

    yes_votes = u_votes['yes']
    no_votes = u_votes['no']

    if yes_votes > no_votes:
        await ctx.send('the majority has voted yes, user will be unmuted')
        role = discord.utils.get(member.guild.roles, name='muted by the people')
        await  member.remove_roles(role)
        
    print(f'{member} has been unmuted')

    if no_votes >= yes_votes:
        await ctx.send('the majority voted no, user will not be unmuted') 

    u_vote = False
    u_votes = {'yes':0, 'no':0}
       
    logger('voteunmute',ctx,False)


@commands.command()
async def giverole(ctx, role_name:str, *, color_code:str):
    logger('giverole',ctx,True)
    
    if color_code == '#000000': # '000000' seems to not behave as expected, therefore it is replaced with '111111' 
        color_code = '#111111'
        print(f'Color Code Exception. Color Replaced With: {color_code}')
    else:
        pass

    color_code = color_code.split('#') # remove the #
    color_code.insert(0, '0x') # replace it with 0x
    color_code = ''.join(color_code) # join the string back
    color_code = int(color_code, 16) # cast to base 16 int

    guild = ctx.guild
    member = ctx.author
    role = discord.utils.get(member.guild.roles, name=role_name)

    if role not in guild.roles: # if role doesnt exist, create it
        await guild.create_role(name=role_name,color=discord.Color(color_code))
    
    if role == None:
        await ctx.send('something went wrong :D')
    
    await member.add_roles(role) # assign the role to the member
    await ctx.send('role added')

    logger('giverole',ctx,False)


@commands.command()
async def removerole(ctx, role_name:str):
    logger('removerole',ctx,True)

    member = ctx.author
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role is None:
        await ctx.send('something went wrong :D')
    else:
        await  member.remove_roles(role)
        await ctx.send('role removed')

    logger('removerole',ctx,False)


@commands.command()
async def wordcloud(ctx):
    logger('wordcloud',ctx,True)
    
    messages = [] 

    for message in bot.cached_messages: # grab all the messages from the bot's internal cache
            messages.append(message.content)

    text = ' '.join(messages)
   
    if os.path.exists('word_cloud.png'): # delete the last word cloud
        os.remove('word_cloud.png')

    wordcloud = WordCloud(max_font_size=50, max_words=500, background_color="white").generate(text) # generate the wordcloud
    plt.figure() # draw the wordcloud
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    wordcloud.to_file('word_cloud.png') # save the wordcloud as an image file

    file = discord.File('word_cloud.png') # create an attachment
    await ctx.channel.send(file=file) # send the attachment
    
    logger('wordcloud',ctx,False)


@commands.group() 
async def meme(ctx):
    if ctx.invoked_subcommand is None: 
        await ctx.send('invalid command :D')


@meme.command()
async def clown(ctx, *, text:str):
    logger('clown',ctx,True)

    img = Image.open('resources/clown.jpg') # get the clown template
    draw = ImageDraw.Draw(img) 
    font = ImageFont.truetype('resources/arial.ttf', 55) # get the font
    image_size = img.size
    lines = text_wrap(text, font, image_size[0]) # split the input text into lines
    line_height = font.getsize('hg')[1] # get height of the lines

    x = 0 # x cordinate of starting position of text
    y = 0 # y cordinate of starting position of text
    color = (0,0,0) # rgb color value of the text
    
    for line in lines:
        # draw the line on the image
        draw.text((x, y), line, fill=color, font=font)
        # update the y position so that we can use it for next line
        y = y + line_height

    img.save('resources/clown_edit.jpg') # save the new image
    file = discord.File('resources/clown_edit.jpg') 
 
    await ctx.channel.send(file=file) # send the new image as an attachment

    logger('clown',ctx,False)


@commands.command()
async def ping(ctx):
    logger('ping',ctx,True)

    latency = bot.latency 
    await ctx.send(latency)
    await ctx.send(':ping_pong:')

    logger('ping',ctx,False)


@commands.command()
async def echo(ctx, n:int, *, content:str):
    logger('echo',ctx,True)
    
    if '@everyone' in content:
        return

    index = 0 # counter
    limit = 15 # maximum number of times to echo text
    if n > 0:
        
        while index < min(n,limit):
            await ctx.send(content)
            index += 1
    else:
        await ctx.send(content)

    logger('echo',ctx,False)


@commands.command()
async def copypasta(ctx, filename, content):
    logger('copypasta',ctx,True)

    try:
        print(f'file name: {filename}')
        print(f'copy pasta: {content}')
        
        dir = f'copypasta/{filename}.txt'
        with open(dir, 'w') as f: # save the copypasta to a text file
           f.write(f'{pasta_string}\n')
    except:
        print('something went wrong :D')

    logger('copypasta',ctx,False)


@commands.command()
async def pasta(ctx, filename):
    logger('pasta',ctx,True)

    dir = f'copypasta/{filename}.txt'
    with open(dir, 'r') as f: # retrieve the copypasta and send it as a message
        pasta = f.read()
        await ctx.send(pasta)

    logger('pasta',ctx,False)


@commands.command()
async def wolfram(ctx, content):
    logger('wolfram',ctx,True)

    wolframAppId = 'APP_ID' # get your app id from here: https://products.wolframalpha.com/simple-api/documentation/
    wolframUrl = 'https://api.wolframalpha.com/v1/result'
    wolframParams = {'i':'{}'.format(content),'appid':'{}'.format(wolframAppId)}

    r = requests.get(wolframUrl, params=wolframParams) # make an http request to get results from wolframalpha with given params
    await ctx.send(r.text) # send results from wolframalpha

    logger('wolfram',ctx,False)


@commands.command()
async def wolfram_image(ctx, content):
    logger('wolfram_image',ctx,True)

    wolframAppId = 'APP_ID' 
    wolframUrl = 'https://api.wolframalpha.com/v1/simple'
    wolframParams = {'i':'{}'.format(content),'appid':'{}'.format(wolframAppId)}

    r = requests.get(wolframUrl, params=wolframParams)
    output = open('data.gif','wb') # save the return as an image
    output.write(r.content)
    output.close()
    attachment = discord.File('data.gif')

    await ctx.channel.send(file=attachment) # send the image as an attachment
    
    logger('wolfram_image',ctx,False)


@commands.command()
async def google(ctx, keywords):
    logger('google',ctx,True)
    
    response = google_images_download.googleimagesdownload()   # class instantiation

    arguments = {"keywords":keywords, "limit":5, "print_urls":False, "safe_search":True}   # creating list of arguments
    paths = response.download(arguments)   # passing the arguments to the function
    attachment = [
    discord.File(paths[0][keywords][random.randint(0,4)]), # get a random image from the 5 results
    ]

    await ctx.send(files=attachment) # send the image as an attachment

    logger('google',ctx,False)


@commands.command()
async def youtube(ctx, url):
    logger('youtube',ctx,True)

    if os.path.exists('source.m4a'): # delete the old sound file
        os.remove('source.m4a')

    def hook(d):
        if d['status'] == 'finished': # display status in console
            print('Done downloading, now converting ...')

    options = { # options passed into youtube_dl
        'restrictfilenames' : 'True',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
        'progress_hooks': [hook] # progress bar
    }

    with youtube_dl.YoutubeDL(options) as ydl: # download audio file from youtube
        ydl.download(['{}'.format(url)])

    for file in os.listdir(os.getcwd()): # rename the file for easier access
        if file.endswith('.m4a'):
            print(file)
            os.rename (str(file), 'source.m4a')
    try:
        channel = ctx.message.author.voice.channel # check if the user is in a voice channel
    
        if not channel:
            await ctx.send('You are not connected to a voice channel')

        voice = get(bot.voice_clients, guild=ctx.guild) # get the voice channel
        if voice and voice.is_connected():
            await voice.move_to(channel) # connect to the same voice channel
        else:
            voice = await channel.connect() 
        source = FFmpegPCMAudio('source.m4a') 
        player = voice.play(source) # play the audio file
    except:
        await ctx.send('You are not connected to a voice channel')

    logger('youtube',ctx,False)


@commands.command()
async def oof(ctx):
    logger('oof',ctx,True)

    try:
        channel = ctx.message.author.voice.channel
        if not channel:
            await ctx.send('You are not connected to a voice channel')

        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
                await voice.move_to(channel)
        else:
            voice = await channel.connect()
        source = FFmpegPCMAudio('sounds/oof.m4a')
        player = voice.play(source)
    except:
        await ctx.send('You are not connected to a voice channel')

    logger('oof',ctx,False)


@commands.command()
async def flip(ctx):
    logger('flip',ctx,True)

    options=['Heads','Tails']
    await ctx.send('You rolled ' + options[random.randint(0,1)])

    logger('flip',ctx,False)


@commands.command()
async def disconnect(ctx):
    logger('disconnect',ctx,True)

    voice = get(bot.voice_clients, guild=ctx.guild)
    await voice.disconnect() # disconnect the bot from a voice channel
    if os.path.exists('source.m4a'):
        os.remove('source.m4a')

    logger('disconnect',ctx,False)


@commands.command()
async def emoji(ctx, *, content:str):
   logger('emoji',ctx,True)

   regular_text=list(content.lower()) # lowercase the input text and cast it to a list
   emoji_text = []

   for i in regular_text: # replace characters with emojis
        if i == '0': 
            emoji_text.append(':zero:')
        elif i == '1': 
            emoji_text.append(':one:')
        elif i == '2': 
            emoji_text.append(':two:')
        elif i == '3': 
            emoji_text.append(':three:')
        elif i == '4': 
            emoji_text.append(':four:')
        elif i == '5': 
            emoji_text.append(':five:')
        elif i == '6': 
            emoji_text.append(':six:')
        elif i == '7': 
            emoji_text.append(':seven:')
        elif i == '8': 
            emoji_text.append(':eight:')
        elif i == '9': 
            emoji_text.append(':nine:')
        elif i == 'b':  # 'b' is replaced with a special :b: emote
            emoji_text.append(':b:')
        elif i == ' ':
            emoji_text.append(' ')
        elif re.search("[a-z]", i): # characters from a-z are replaced with :regional_indicator_{char}: emote
            emoji_text.append(':regional_indicator_{}:'.format(i))
        else:
            emoji_text.append(i)

   emoji_text = ' '.join(emoji_text) # list to string
   await ctx.send(emoji_text)

   logger('emoji',ctx,False)


@commands.command()
async def help(ctx):
    logger('help',ctx,True)

    embed = discord.Embed(title='Available Commands')

    embed.add_field(name='!ping', value='returns the ping', inline = False)
    embed.add_field(name='!echo', value='usage: !echo [number of times to echo] [text to echo]', inline = False)
    embed.add_field(name='!giverole', value='usage: !giverole "name here" [html color code]', inline = False)
    embed.add_field(name='!removerole', value='usage: !removerole "name here"', inline = False)
    embed.add_field(name='!flip', value='flips a coin', inline = False)
    embed.add_field(name='!copypasta', value='usage: !copypasta [name] [copypasta here]', inline = False)
    embed.add_field(name='!pasta', value='recall the copypasta, !pasta [name]')
    embed.add_field(name='!emoji', value='emojifys the text', inline = False)
    embed.add_field(name='!wordcloud', value='generates a wordcloud', inline = False)
    embed.add_field(name='!wolfram', value='wolfram search', inline = False)
    embed.add_field(name='!wolfram_image', value='wolfram search but returns an image', inline = False)
    embed.add_field(name='!google', value='usage: !google [keywords]', inline = False)
    embed.add_field(name='!oof', value='plays /sound/oof.m4a', inline = False)
    embed.add_field(name='!youtube', value='usage: !youtube [youtube link]', inline = False)
    embed.add_field(name='!disconnect', value='disconnects the bot from the voice channel', inline = False)
    embed.add_field(name='!meme clown', value='usage: !clown (text)', inline = False)
    embed.add_field(name='!votemute', value='usage: !votemute (tag the user to mute)', inline = False)
    embed.add_field(name='!voteunmute', value='usage: !voteunmute (tag the user to mute)', inline = False)

    await ctx.send(embed=embed)

    logger('help',ctx,False)

 
def main():
    if len(sys.argv) < 2:
        print(f'ERROR 0: No Client Token Provided')
        sys.exit

    bot.add_command(ping)
    bot.add_command(echo)
    bot.add_command(giverole)
    bot.add_command(removerole)
    bot.add_command(flip)
    bot.add_command(copypasta)
    bot.add_command(pasta)
    bot.add_command(emoji)
    bot.add_command(wordcloud)
    bot.add_command(wolfram)
    bot.add_command(wolfram_image)
    bot.add_command(google)
    bot.add_command(youtube)
    bot.add_command(disconnect)
    bot.add_command(clown)
    bot.add_command(oof)
    bot.add_command(meme)
    bot.add_command(votemute)
    bot.add_command(voteunmute)
    bot.add_command(reset)
    bot.add_command(update)

    bot_token = sys.argv[1]
    bot.run(bot_token)

if __name__ == "__main__":
    main()
