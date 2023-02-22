
from discord import Interaction

async def send(interaction:Interaction, *args, **kwargs):
    await interaction.response.send_message(*args, **kwargs)

async def followup(interaction:Interaction, *args, **kwargs):
    await interaction.followup.send(*args, **kwargs)

async def edit_original(interaction:Interaction, *args, **kwargs):
    await interaction.edit_original_response(*args, **kwargs)
