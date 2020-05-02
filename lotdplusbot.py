# bot.py
import os
import time
import discord
import tempfile
import shutil
from urllib.request import urlopen, Request
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
STAFF_CHANNEL = os.getenv('STAFF_CHANNEL')
MOD_ROLE = os.getenv('MOD_ROLE')
ADMIN_ROLE = os.getenv('ADMIN_ROLE')
OWNER_ID = os.getenv('OWNER_ID')

client = discord.Client()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
enabled = True

@client.event
async def on_ready():
    print(f'{client.user} is now connected')
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!loadorder"):
        # Help menu
        if message.content.startswith("!loadorder help"):
            if str(message.channel.id) == STAFF_CHANNEL:
                await message.channel.send(staffhelp())
            else:
                await message.channel.send(help())
            return
        # Check if message sent in staff channel
        if str(message.channel.id) == STAFF_CHANNEL:
            # Staff command to pause
            if message.content.startswith("!loadorder pause"):
                for role in message.author.roles:
                    if str(role.id) == ADMIN_ROLE or str(role.id) == MOD_ROLE:
                        pause()
                        await message.channel.send("Load order validation paused")                      
                if str(message.author.id) == OWNER_ID:
                    pause()
                    await message.channel.send("Load order validation paused")
                return
            # Staff command to resume
            if message.content.startswith("!loadorder resume"):
                for role in message.author.roles:
                    if str(role.id) == ADMIN_ROLE or str(role.id) == MOD_ROLE:
                        resume()
                        await message.channel.send("Load order validation resumed")
                if str(message.author.id) == OWNER_ID:
                    resume()
                    await message.channel.send("Load order validation resumed")
                return
            # Staff command to update the master list
            if message.content.startswith("!loadorder update"):
                for role in message.author.roles:
                    if str(role.id) == ADMIN_ROLE or str(role.id) == MOD_ROLE:
                        if len(message.attachments) == 1 and message.attachments[0].filename == "loadorder.txt":
                            update(message.attachments[0].url)
                            await message.channel.send("Load order successfully updated")
                        else:
                            await message.channel.send("Must have exactly 1 attachment named loadorder.txt")
                if str(message.author.id) == OWNER_ID:
                    if len(message.attachments) == 1 and message.attachments[0].filename == "loadorder.txt":
                        update(message.attachments[0].url)
                        await message.channel.send("Load order successfully updated")
                    else:
                        await message.channel.send("Must have exactly 1 attachment named loadorder.txt")
                return
            # Staff command to get information about the bot & load order
            if message.content.startswith("!loadorder status"):
                for role in message.author.roles:
                    if str(role.id) == ADMIN_ROLE or str(role.id) == MOD_ROLE:
                        await message.channel.send(status())
                if str(message.author.id) == OWNER_ID:
                   await message.channel.send(status())
                return
        # Check if bot is paused
        global enabled  
        if not enabled:
                await message.channel.send("The bot is currently paused due to the recent update")
        # Check if they attached file
        elif len(message.attachments) == 1:
            if message.attachments[0].filename == "loadorder.txt":
                reg_url = message.attachments[0].url
                req = Request(url=reg_url, headers=headers)
                secondary = open(prepareSecondary(req), "r")
                await message.channel.send("Here's what to fix:")
                tempfile = open("temp_diff.txt", "w")
                master = open("loadorder.txt", "r")
                tempfile.write(compare(master,secondary))
                master.close()
                tempfile.close()
                secondary.close()
                with open('temp_diff.txt', 'rb') as fp:
                    await message.channel.send(file=discord.File(fp, 'differences.txt'))
            else:
                await message.channel.send("File name must be loadorder.txt")
        else:
            await message.channel.send("You must attach your loadorder.txt file in the same message as !loadorder\n" +
                                       "The file is located at `MO2/profiles/LOTDPlus/loadorder.txt`")

def prepareSecondary(req):
    with urlopen(req) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
            return os.path.abspath(tmp_file.name)

def compare(master, secondary):
    masterLines = [string.lower()[:string.index("\n")] for string in master.readlines()]
    compareLines = [string.lower()[:string.index("\n")] for string in secondary.readlines()]

    msg = "Your load order is missing:\n"
    for line in masterLines:
        if not line in compareLines:
            msg += str(line)
            # Files generated during finishing line
            if line == "dyndolod.esm" or line == "bashed patch, 0.esp" or line == "smashed patch.esp" or line == "lexy's lotd se omega - smash override.esp" or line == "enblight patch.esp" or line == "know_your_armor_patch.esp" or line == "know_your_enemy_patch.esp" or line == "lunarweaponspatch.esp" or line == "zpatch.esp" or line == "dyndolod.esp" or line == "occlusion.esp" or line == "fnis.esp":
                msg += " - Finishing line"
            # Audio settings optional file
            if line == "lsfx-sse-audiosettings.esp":
                msg += " - This one is optional"
            msg += "\n"
    msg += "\nThese should not be in your load order:\n"
    for line in compareLines:
        if not line in masterLines:
            msg += str(line)
            # Special instructions - ESP Deletion
            # Page 1 of mod installs
            if line == "dragon stalking fix.esp" or line == "hornsareforever.esp" or line == "hd lods sse.esp":
                msg += " - Special instructions: Delete this"
            # Page 2 of mod installs
            if line == "particle patch for enb sse.esp" or (line.startswith("solitudetemplefrescoes") and not line == "solitudetemplefrescoesbig.esp") or line == "enhanced landscapes.esp" or line == "skyrim flora overhaul.esp" or line == "sfo - dragonborn.esp":
                msg += " - Special instructions: Delete this"
            # Page 3 UP TO Kalilie's NPCs
            if line == "wico - immersive character.esp" or line == "wico - immersive dawnguard.esp" or line == "wico - immersive people.esp" or line == "fhh_legendary_ve_ussep.esp" or line == "metalsabers beutiful orcs of skyrim.esp" or line == "the ordinary women.esp" or line == "pan_npcs.esp" or line == "kaliliesnpcs.esp":
                msg += " - Special instructions: Delete this"
            # Page 3 UP TO Valerica
            if line == "fresh faces - ussep.esp" or line == "pan_npcs_dg.esp" or line == "pan_npcs_db.esp" or line == "bijin warmaidens.esp" or line == "bijin wives.esp" or line == "bijin npcs.esp" or line == "serana.esp" or line == "valerica.esp":
                msg += " - Special instructions: Delete this"
            # Eeekie's Enhanced NPCs
            if line == "alvor replacement v2.esp" or line == "eeekie's balimund replacer.esp" or line == "eeekie's brynjolf.esp" or line == "eeekie elisif replacer.esp" or line == "eeekie's farengar.esp" or line == "idgrod replacer.esp" or line == "eeekie's young idgrod replacer.esp" or line == "eeekie's jon battle born.esp" or line == "eeekie's laila law giver.esp" or line == "eeekie's siddegir replacer.esp" or line == "tolfdirv2.esp" or line == "eeekie's viarmo.esp":
                msg += " - Special instructions: Delete this"
            # Rest of page 3 of mod installs
            if line == "rdo - ussep patch.esp" or line == "cuyima 3dnpc - redone.esp" or line == "3dnpc_frogcustom_zora.esp" or line == "gqj_dg_vampireamuletfix.esp" or line == "cloaks - ussep patch.esp" or line == "hothtrooper44_armor_ecksstra.esp" or line.startswith("lore weapon expansion - ") or line.startswith("hunterborn - "):
                msg += " - Special instructions: Delete this"
            # Page 4 of mod installs
            if line == "waccf_bashedpatchlvllistfix.esp" or line == "omega ars metallica caco patch.esp" or line == "omega beyond skyrim dlc caco patch.esp" or line == "omega kye caco lite patch.esp" or line == "omega kye caco patch.esp" or line == "omega lotd caco.esp" or line == "omega vigor caco patch.esp":
                msg += " - Special instructions: Delete this"

            # Misc common mistakes
            # ITS ALWAYS BROWS!!!
            if line == "brows.esp":
                msg += " - Wrong FOMOD option"
            # City Entrances Overhaul
            if line == "ceowindhelm - icaio patch [esl].esp":
                msg += " - Special instructions: Use replacer ESP"
            # moreHUD Inventory Edition
            if line == "ahzmorehudinventory.esl":
                msg += " - moreHUD Inventory Edition: You picked the wrong download"
            # CACO SIC Patch from patch hub
            if line == "caco_skyrimimmersivecreasuresse_patch.esp":
                msg += " - Delete this (shouldn't have selected in patch hub fomod)"

            # Merge mistakes
            # Lawbringer
            if line.startswith("lco_") and not line == "lco_framework.esp":
                msg += " - Should be in Pre Bash Merged"
            msg += "\n"

    return msg

def pause():
    global enabled
    enabled = False

def resume():
    global enabled
    enabled = True

def update(url_in):
    req = Request(url=url_in, headers=headers)
    with urlopen(req) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
    shutil.copy(os.path.abspath(tmp_file.name), "loadorder.txt")

def status():
    global enabled
    if enabled:
        msg = "Load order validation is currently enabled\n"
    else:
        msg = "Load order validation is currently disabled\n"
    modTime = os.path.getmtime("loadorder.txt")
    stringTime = time.ctime(modTime)
    msg += "The load order was last updated on `"
    msg += stringTime + "`"
    return msg

def help():
    msg = "This bot will validate your load order for you\n"
    msg += "It does this by comparing your load order against a master list\n"
    msg += "To use it, type `!loadorder` and upload your load order (in the same message)\n"
    msg += "Your load order can be found at `MO2/profiles/LOTDPlus/loadorder.txt`\n"
    msg += "I will respond with a text file containg what you need to change\n"
    msg += "Some common mistakes have reasons already listed"
    return msg

def staffhelp():
    msg = "The use of these commands is limited to RoboticPlayer, as well as users with the `Moderator` and `Admin` role\n"
    msg += "!loadorder pause - Disables load order validation (used when an update comes out until the load order is updated)\n"
    msg += "!loadorder resume - Enables load order validation (use after upading the load order)\n"
    msg += "!loadorder update - Updates the master file with the attached file\n"
    msg += "!loadorder status - Tells you if validation is enabled or disabled, as well as the last loadorder update time\n"
    msg += "Running !loadorder help outside of the staff channel will display how to use the bot"
    return msg

client.run(TOKEN)
