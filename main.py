import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import aiohttp  # async HTTP client for POST requests
from datetime import datetime
from dotenv import load_dotenv
from aiohttp import web

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 8080))

# Your Google Apps Script webhook URL here (from deploying the Apps Script web app)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # put your webhook URL in .env or replace here directly

# Discord IDs
LOG_CHANNEL_ID = 1395509672852852836
WELCOME_CHANNEL_ID = 1286494224677736471
INVITE_LINK = "https://discord.gg/dm8yXHD4"
WELCOME_GIF_URL = "https://www.dropbox.com/scl/fi/yxya94d102ltsrz64qv9k/Photo-Jul-16-2025-22-48-40.gif?rlkey=1bs2wfc8ae0tuax8deyo6crwy&st=lqux5oe7&raw=1"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

user_role_choices = {}

class RegistrationModal(discord.ui.Modal, title="WMI Registration"):
    name = discord.ui.TextInput(label="Full Name", placeholder="Enter your full name", required=True)
    email = discord.ui.TextInput(label="Email", placeholder="Enter your email (optional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        email = self.email.value or "Not provided"

        # Send data to Google Apps Script webhook
        data = {
            "name": name,
            "email": email,
            "role": "MS1 Year 1 Student",
            "discord_user": str(interaction.user),
            "discord_id": str(interaction.user.id),
            "timestamp": datetime.utcnow().isoformat()
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(WEBHOOK_URL, json=data) as resp:
                    if resp.status == 200:
                        print("✅ Data sent to Google Sheets via webhook")
                    else:
                        print(f"⚠️ Failed to send data: {resp.status}")
            except Exception as e:
                print(f"Exception sending webhook: {e}")

        # Show role selection button
        view = RoleView(interaction.user.id)
        role_embed = discord.Embed(
            title="Choose Your Role",
            description="Click the button below to select your role at Wisteria Medical Institute.",
            color=discord.Color.from_str("#B19CD9")
        )
        await interaction.response.send_message(embed=role_embed, view=view, ephemeral=True)

        # Log in Discord channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📝 New Student Registration Logged",
                color=discord.Color.from_str("#7D5BA6")
            )
            log_embed.add_field(name="👤 Name", value=name, inline=True)
            log_embed.add_field(name="📧 Email", value=email, inline=True)
            log_embed.add_field(name="🆔 Discord", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            log_embed.add_field(name="🎓 Role", value="MS1 Year 1 Student", inline=True)
            log_embed.add_field(name="🕒 Date (UTC)", value=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), inline=True)
            await log_channel.send(embed=log_embed)

class RoleButton(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(label="MS1 Year 1 Student", style=discord.ButtonStyle.primary)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            user_role_choices[self.user_id] = 1386056949602455683  # Replace with your actual role ID
            embed = discord.Embed(
                title="✅ Role Selected!",
                description=(
                    f"You’ve selected **MS1 Year 1 Student**!\n\n"
                    f"🌐 Click here to join the Wisteria medical institute community:\n{INVITE_LINK}"
                ),
                color=discord.Color.from_str("#C9A0DC")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.add_item(RoleButton(user_id))

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Sync failed: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    role_id = user_role_choices.pop(member.id, None)
    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Error assigning role: {e}")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🌸 Welcome to Wisteria Medical Institute!",
            description=(
                f"Greetings, <@{member.id}>!\n\n"
                "On behalf of our Leadership Council, we are absolutely **thrilled** to have you join our community!\n\n"
                "At **Wisteria Medical Institute**, we're dedicated to providing realistic medical education courses "
                "and lessons while fostering an inclusive environment for all students and staff. Whether you're here "
                "to **learn**, **teach**, or **make friends**, we're excited to have you with us. 💜\n\n"
                "We can't wait to see all that you'll accomplish!\n\n"
                " To gain full access to our community channels, please make sure to verify in <#1390781451812999349>.\n\n"
                " Need assistance? Open a ModMail ticket. More information can be found in <#1390777039736537169>.\n\n"
                "<:WMILogo:1393624412036534423>  **Wisteria Medical Institute** — All Rights Reserved."
            ),
            color=discord.Color.from_str("#B19CD9")
        )
        embed.set_image(url=WELCOME_GIF_URL)
        embed.set_footer(text="Wisteria Medical Institute", icon_url="https://i.imgur.com/zjXe9Rv.png")
        await channel.send(embed=embed)

@app_commands.command(name="wmi_register", description="Register for Wisteria Medical Institute")
async def wmi_register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

bot.tree.add_command(wmi_register)

# Simple web server to keep bot alive (optional)
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Web server started on port {PORT}")

async def main():
    await asyncio.gather(
        bot.start(DISCORD_TOKEN),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
