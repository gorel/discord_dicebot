import random
import os
import discord
import json

from discord.ext import commands

client = commands.Bot(command_prefix="*")
client.remove_command('help')

r6_atk = ['SLEDGE', 'THATCHER', 'ASH', 'THERMITE', 'MICK', 'TICK', 'BLITZ', 'IQ', 'FUZE', 'GLAZ', 'BUCK', 'BLACKBEARD', 'CAPITAO', 'HIBANA', 'JACKAL', 'YING', 'ZOFIA', 'DOKKAEBI', 'FINKA', 'LION', 'MAVERICK', 'NOMAD', 'GRIDLOCK', 'NØKK', 'AMARU', 'KALI']

r6_def = ['MUTE', 'SMONK', 'CASTLE', 'PULSE', 'DICK', 'RICK', 'JÄGER', 'BANDIT', 'GOD', 'KAPKAN', 'FROST', 'VALKYRIE', 'CAVEIRA', 'ECHO', 'MIRA', 'LESION', 'ELA', 'VIGIL', 'ALIBI', 'MAESTRO', 'CLASH', 'KAID', 'MOZZIE', 'WARDEN', 'GOYO', 'WAMAI']


@client.event
async def on_ready():
    print("Bot is online!")


@client.event
async def on_message(message):
    userID = str(message.author.id)

    with open('user_data.json', 'r') as infile:
        removed_operators = json.load(infile)

    if userID not in removed_operators:
        removed_operators[userID] = []

        with open('user_data.json', 'w') as outfile:
            json.dump(removed_operators, outfile)

        outfile.close()

    await client.process_commands(message)


@client.command()
async def picka(ctx):
    userID = str(ctx.message.author.id)
    attacker_pick = random.choice(r6_atk)

    while await check_operators(userID, attacker_pick):
        attacker_pick = random.choice(r6_atk)

    await ctx.send(attacker_pick)


@client.command()
async def pickd(ctx):
    userID = str(ctx.message.author.id)
    defender_pick = random.choice(r6_def)

    while await check_operators(userID, defender_pick):
        defender_pick = random.choice(r6_atk)

    await ctx.send(defender_pick)


@client.command()
async def disable(ctx, *, arg):
    userID = str(ctx.message.author.id)
    operators = arg.upper().split()

    with open('user_data.json', 'r') as infile:
        removed_operators = json.load(infile)

    for op in operators:
        if op in r6_atk or op in r6_def:
            removed_operators[userID].append(op)
        else:
            await ctx.send(f"I'm sorry, I don't recognize {op}")
            operators.remove(op)

    with open('user_data.json', 'w') as outfile:
        json.dump(removed_operators, outfile)

    outfile.close()

    await ctx.send(f"Your Disabled Operators: {removed_operators[userID]}")


@client.command()
async def enable(ctx, *, arg):
    userID = str(ctx.message.author.id)
    operators = arg.upper().split()

    with open('user_data.json', 'r') as infile:
        removed_operators = json.load(infile)

    for op in operators:
        if op in removed_operators[userID]:
            removed_operators[userID].remove(op)
        elif op in r6_atk or op in r6_def:
            await ctx.send(f"You have not disabled {op}")
            operators.remove(op)
        else:
            await ctx.send(f"I'm sorry, I don't recognize {op}")
            operators.remove(op)

    with open('user_data.json', 'w') as outfile:
        json.dump(removed_operators, outfile)

    outfile.close()

    if len(operators) > 1:
        await ctx.send(f"Enabled Operators: {operators}")
    else:
        await ctx.send(f"Enabled Operator: {operators}")


async def check_operators(userID, operator_pick):
    with open('user_data.json', 'r') as infile:
        removed_operators = json.load(infile)

    if operator_pick in removed_operators[userID]:
        return True
    else:
        return False

client.run("TEST_BOT_TOKEN")
