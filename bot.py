import asyncio
import datetime
import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

ACTIVE_GIVEAWAYS = {}

NEXUS_BLUE = discord.Color.from_rgb(15, 34, 64)

class GiveawayButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.primary,
        emoji="🎉",
        custom_id="nexus_giveaway_enter"
    )
    async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        giveaway = ACTIVE_GIVEAWAYS.get(message_id)

        if not giveaway:
            await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
            return

        if giveaway["ended"]:
            await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in giveaway["participants"]:
            giveaway["participants"].remove(user_id)
            action_msg = "You have left the giveaway."
        else:
            giveaway["participants"].add(user_id)
            action_msg = "You have successfully entered the giveaway! 🎉"

import asyncio
import datetime
import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.default()
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

ACTIVE_GIVEAWAYS = {}

NEXUS_BLUE = discord.Color.from_rgb(15, 34, 64)

class GiveawayButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Giveaway",
        style=discord.ButtonStyle.primary,
        emoji="🎉",
        custom_id="nexus_giveaway_enter"
    )
    async def enter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        giveaway = ACTIVE_GIVEAWAYS.get(message_id)

        if not giveaway:
            await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
            return

        if giveaway["ended"]:
            await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in giveaway["participants"]:
            giveaway["participants"].remove(user_id)
            action_msg = "You have left the giveaway."
        else:
            giveaway["participants"].add(user_id)
            action_msg = "You have successfully entered the giveaway! 🎉"

        await update_giveaway_embed(interaction.message, giveaway)
        await interaction.response.send_message(action_msg, ephemeral=True)

async def update_giveaway_embed(message: discord.Message, giveaway: dict):
    embed = message.embeds[0]
    embed.set_field_at(
        index=3,
        name="Participants",
        value=str(len(giveaway["participants"])),
        inline=True
    )
    await message.edit(embed=embed)

@BOT.event
async def on_ready():
    BOT.add_view(GiveawayButton())
    check_giveaways.start()
    print(f"Logged in as {BOT.user.name} ({BOT.user.id})")
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

@tasks.loop(seconds=5)
async def check_giveaways():
    now = datetime.datetime.now(datetime.timezone.utc)
    to_end = []
    for msg_id, g in ACTIVE_GIVEAWAYS.items():
        if not g["ended"] and now >= g["end_time"]:
            to_end.append(msg_id)

    for msg_id in to_end:
        giveaway = ACTIVE_GIVEAWAYS[msg_id]
        giveaway["ended"] = True
        channel = giveaway["channel"]
        try:
            msg = await channel.fetch_message(msg_id)
            view = GiveawayButton()
            for child in view.children:
                child.disabled = True
            
            embed = msg.embeds[0]
            embed.color = discord.Color.dark_embed()
            embed.add_field(name="Status", value="Ended (Pending Winner Selection)", inline=False)
            await msg.edit(embed=embed, view=view)
        except Exception as e:
            print(f"Failed to auto-end giveaway {msg_id}: {e}")

@BOT.tree.command(name="gstart", description="Start a new Nexus eSports giveaway.")
@app_commands.describe(
    prize="The prize being given away",
    duration="Duration in minutes",
    winners="Number of winners"
)
@app_commands.checks.has_permissions(administrator=True)
async def gstart(interaction: discord.Interaction, prize: str, duration: int, winners: int):
    if duration <= 0 or winners <= 0:
        await interaction.response.send_message("Duration and winners must be greater than 0.", ephemeral=True)
        return

    end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=duration)
    timestamp = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 NEXUS ESPORTS GIVEAWAY 🎉",
        description=f"**Prize:** {prize}",
        color=NEXUS_BLUE
    )
    embed.add_field(name="Host", value=interaction.user.mention, inline=True)
    embed.add_field(name="Winners", value=str(winners), inline=True)
    embed.add_field(name="Ends At", value=f"<t:{timestamp}:R> (<t:{timestamp}:F>)", inline=False)
    embed.add_field(name="Participants", value="0", inline=True)
    embed.set_footer(text="Nexus eSports Giveaways")

    view = GiveawayButton()
    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()

    ACTIVE_GIVEAWAYS[message.id] = {
        "prize": prize,
        "host": interaction.user,
        "channel": interaction.channel,
        "end_time": end_time,
        "winners_count": winners,
        "participants": set(),
        "ended": False,
        "winners": []
    }

@BOT.tree.command(name="gend", description="End an active giveaway early.")
@app_commands.describe(message_id="The message ID of the giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def gend(interaction: discord.Interaction, message_id: str):
    try:
        msg_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("Invalid Message ID.", ephemeral=True)
        return

    giveaway = ACTIVE_GIVEAWAYS.get(msg_id)
    if not giveaway or giveaway["ended"]:
        await interaction.response.send_message("Active giveaway not found with that ID.", ephemeral=True)
        return

    giveaway["ended"] = True
    channel = giveaway["channel"]
    try:
        msg = await channel.fetch_message(msg_id)
        view = GiveawayButton()
        for child in view.children:
            child.disabled = True
        
        embed = msg.embeds[0]
        embed.color = discord.Color.dark_embed()
        embed.add_field(name="Status", value="Ended Early", inline=False)
        await msg.edit(embed=embed, view=view)
        await interaction.response.send_message(f"Giveaway for **{giveaway['prize']}** has been ended early.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error ending giveaway: {e}", ephemeral=True)

@BOT.tree.command(name="greroll", description="Reroll winner(s) for a completed giveaway.")
@app_commands.describe(message_id="The message ID of the giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def greroll(interaction: discord.Interaction, message_id: str):
    try:
        msg_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("Invalid Message ID.", ephemeral=True)
        return

    giveaway = ACTIVE_GIVEAWAYS.get(msg_id)
    if not giveaway or not giveaway["ended"]:
        await interaction.response.send_message("Giveaway not found or has not ended yet.", ephemeral=True)
        return

    participants = list(giveaway["participants"])
    if not participants:
        await interaction.response.send_message("No participants entered this giveaway.", ephemeral=True)
        return

    count = min(giveaway["winners_count"], len(participants))
    winner_ids = random.sample(participants, count)
    winners = [interaction.guild.get_member(uid) or await BOT.fetch_user(uid) for uid in winner_ids]
    giveaway["winners"] = winners

    winners_mention = ", ".join([w.mention for w in winners])
    await interaction.channel.send(f"🔄 **REROLL!** New winner(s) for **{giveaway['prize']}**: {winners_mention}!")
    await interaction.response.send_message("Successfully rerolled new winner(s).", ephemeral=True)

@BOT.tree.command(name="gwinner", description="Select and announce the winner(s) for a giveaway.")
async def gwinner(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_modal(WinnerModal())

class WinnerModal(discord.ui.Modal, title="Select Giveaway Winner"):
    message_id_input = discord.ui.TextInput(
        label="Giveaway Message ID",
        placeholder="Paste the message ID of the giveaway...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            msg_id = int(self.message_id_input.value)
        except ValueError:
            await interaction.response.send_message("Invalid Message ID.", ephemeral=True)
            return

        giveaway = ACTIVE_GIVEAWAYS.get(msg_id)
        if not giveaway:
            await interaction.response.send_message("Giveaway not found in memory.", ephemeral=True)
            return

        participants = list(giveaway["participants"])
        if not participants:
            await interaction.response.send_message("No participants entered this giveaway.", ephemeral=True)
            return

        count = min(giveaway["winners_count"], len(participants))
        winner_ids = random.sample(participants, count)
        winners = [interaction.guild.get_member(uid) or await BOT.fetch_user(uid) for uid in winner_ids]
        giveaway["winners"] = winners
        giveaway["ended"] = True

        winners_mention = ", ".join([w.mention for w in winners])
        
        await giveaway["channel"].send(f"🎉 **GIVEAWAY WINNER(S)!** Congratulations {winners_mention}! You won **{giveaway['prize']}**!")
        await interaction.response.send_message(f"Winners selected and announced: {winners_mention}", ephemeral=True)

@BOT.tree.command(name="glist", description="Show currently active giveaways.")
async def glist(interaction: discord.Interaction):
    if not ACTIVE_GIVEAWAYS:
        await interaction.response.send_message("There are no active giveaways right now.", ephemeral=True)
        return

    embed = discord.Embed(title="Active Giveaways", color=NEXUS_BLUE)
    for msg_id, g in ACTIVE_GIVEAWAYS.items():
        if not g["ended"]:
            timestamp = int(g["end_time"].timestamp())
            embed.add_field(
                name=g["prize"],
                value=f"ID: `{msg_id}`\nHost: {g['host'].mention}\nEnds: <t:{timestamp}:R>\nParticipants: {len(g['participants'])}",
                inline=False
            )

    if len(embed.fields) == 0:
        await interaction.response.send_message("There are no active giveaways right now.", ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

@BOT.tree.command(name="ghelp", description="Show available giveaway commands.")
async def ghelp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Nexus eSports Giveaway Commands",
        description="Here are the available commands for managing giveaways:",
        color=NEXUS_BLUE
    )
    embed.add_field(name="/gstart", value="Start a giveaway (Admin only)", inline=False)
    embed.add_field(name="/gend", value="End an active giveaway early (Admin only)", inline=False)
    embed.add_field(name="/greroll", value="Pick new winner(s) (Admin only)", inline=False)
    embed.add_field(name="/gwinner", value="Select and announce winners (Admin only)", inline=False)
    embed.add_field(name="/glist", value="List all active giveaways", inline=False)
    embed.add_field(name="/ghelp", value="Show this help message", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        BOT.run(TOKEN)
￼Enter        await update_giveaway_embed(interaction.message, giveaway)
        await interaction.response.send_message(action_msg, ephemeral=True)

async def update_giveaway_embed(message: discord.Message, giveaway: dict):
    embed = message.embeds[0]
    embed.set_field_at(
        index=3,
        name="Participants",
        value=str(len(giveaway["participants"])),
        inline=True
    )
    await message.edit(embed=embed)

@BOT.event
async def on_ready():
    BOT.add_view(GiveawayButton())
    check_giveaways.start()
    print(f"Logged in as {BOT.user.name} ({BOT.user.id})")
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)

@tasks.loop(seconds=5)
async def check_giveaways():
    now = datetime.datetime.now(datetime.timezone.utc)
    to_end = []
    for msg_id, g in ACTIVE_GIVEAWAYS.items():
        if not g["ended"] and now >= g["end_time"]:
            to_end.append(msg_id)

    for msg_id in to_end:
        giveaway = ACTIVE_GIVEAWAYS[msg_id]
        giveaway["ended"] = True
        channel = giveaway["channel"]
        try:
            msg = await channel.fetch_message(msg_id)
            view = GiveawayButton()
            for child in view.children:
                child.disabled = True
            
            embed = msg.embeds[0]
            embed.color = discord.Color.dark_embed()
            embed.add_field(name="Status", value="Ended (Pending Winner Selection)", inline=False)
            await msg.edit(embed=embed, view=view)
        except Exception as e:
            print(f"Failed to auto-end giveaway {msg_id}: {e}")

@BOT.tree.command(name="gstart", description="Start a new Nexus eSports giveaway.")
@app_commands.describe(
    prize="The prize being given away",
    duration="Duration in minutes",
    winners="Number of winners"
)
@app_commands.checks.has_permissions(administrator=True)
async def gstart(interaction: discord.Interaction, prize: str, duration: int, winners: int):
    if duration <= 0 or winners <= 0:
        await interaction.response.send_message("Duration and winners must be greater than 0.", ephemeral=True)
        return

    end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=duration)
    timestamp = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 NEXUS ESPORTS GIVEAWAY 🎉",
        description=f"**Prize:** {prize}",
        color=NEXUS_BLUE
    )
    embed.add_field(name="Host", value=interaction.user.mention, inline=True)
    embed.add_field(name="Winners", value=str(winners), inline=True)
    embed.add_field(name="Ends At", value=f"<t:{timestamp}:R> (<t:{timestamp}:F>)", inline=False)
    embed.add_field(name="Participants", value="0", inline=True)
    embed.set_footer(text="Nexus eSports Giveaways")

    view = GiveawayButton()
    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()
CTIVE_GIVEAWAYS[message.id] = {
        "prize": prize,
        "host": interaction.user,
        "channel": interaction.channel,
        "end_time": end_time,
        "winners_count": winners,
        "participants": set(),
        "ended": False,
        "winners": []
    }

@BOT.tree.command(name="gend", description="End an active giveaway early.")
@app_commands.describe(message_id="The message ID of the giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def gend(interaction: discord.Interaction, message_id: str):
    try:
        msg_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("Invalid Message ID.", ephemeral=True)
        return

    giveaway = ACTIVE_GIVEAWAYS.get(msg_id)
    if not giveaway or giveaway["ended"]:
        await interaction.response.send_message("Active giveaway not found with that ID.", ephemeral=True)
        return

    giveaway["ended"] = True
    channel = giveaway["channel"]
    try:
        msg = await channel.fetch_message(msg_id)
        view = GiveawayButton()
        for child in view.children:
            child.disabled = True
        
        embed = msg.embeds[0]
        embed.color = discord.Color.dark_embed()
        embed.add_field(name="Status", value="Ended Early", inline=False)
        await msg.edit(embed=embed, view=view)
        await interaction.response.send_message(f"Giveaway for **{giveaway['prize']}** has been ended early.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error ending giveaway: {e}", ephemeral=True)

@BOT.tree.command(name="greroll", description="Reroll winner(s) for a completed giveaway.")
@app_commands.describe(message_id="The message ID of the giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def greroll(interaction: discord.Interaction, message_id: str):
    try:
        msg_id = int(message_id)
    except ValueError:
        await interaction.response.send_message("Invalid Message ID.", ephemeral=True)
        return

    giveaway = ACTIVE_GIVEAWAYS.get(msg_id)
    if not giveaway or not giveaway["ended"]:
        await interaction.response.send_message("Giveaway not found or has not ended yet.", ephemeral=True)
        return

    participants = list(giveaway["participants"])
    if not participants:
        await interaction.response.send_message("No participants entered this giveaway.", ephemeral=True)
        return

    count = min(giveaway["winners_count"], len(participants))
    winner_ids = random.sample(participants, count)
    winners = [interaction.guild.get_member(uid) or await BOT.fetch_user(uid) for uid in winner_ids]
    giveaway["winners"] = winners

    winners_mention = ", ".join([w.mention for w in winners])
    await interaction.channel.send(f"🔄 **REROLL!** New winner(s) for **{giveaway['prize']}**: {winners_mention}!")
    await interaction.response.send_message("Successfully rerolled new winner(s).", ephemeral=True)

@BOT.tree.command(name="gwinner", description="Select and announce the winner(s) for a giveaway.")
async def gwinner(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

