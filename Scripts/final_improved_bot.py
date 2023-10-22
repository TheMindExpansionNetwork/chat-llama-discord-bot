# Imports and Setup
import os

# Use Environment Variables for Sensitive Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'your_default_bot_token_here')


# Here, various Python libraries and modules necessary for the bot functionality are imported.

from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
import asyncio
import random
import json
import re
import copy
import logging
import math
import glob
import os
import yaml
import warnings
import discord
from discord.ext import commands
from discord import app_commands
import torch

logger = logging.getLogger("discord")
logger.propagate = False

# Intercept custom bot arguments
import sys

# Argument Parsing
# This section is responsible for parsing command-line arguments to configure the bot.

bot_arg_list = ["--limit-history", "--token"]
bot_argv = []
for arg in bot_arg_list:
    try:
        index = sys.argv.index(arg)
    except:
        index = None
    
    if index is not None:
        bot_argv.append(sys.argv.pop(index))
        bot_argv.append(sys.argv.pop(index))

import argparse
parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=54))
parser.add_argument("--token", type=str, help="Discord bot token to use their API.")
parser.add_argument("--limit-history", type=int, help="When the history gets too large, performance issues can occur. Limit the history to improve performance.")
bot_args = parser.parse_args(bot_argv)

os.environ["BITSANDBYTES_NOWELCOME"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, message="TypedStorage is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, message="You have modified the pretrained model configuration to control generation")

import modules.extensions as extensions_module
from modules.chat import generate_chat_reply, clear_chat_log, load_character
from modules import shared, utils
shared.args.chat = True
from modules.LoRA import add_lora_to_model
from modules.models import load_model

TOKEN = "<token here>"

reply_embed_json = {
    "title": "Reply #X",
    "color": 39129,
    "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
    "url": "https://github.com/xNul/chat-llama-discord-bot",
    "footer": {
        "text": "Contribute to ChatLLaMA on GitHub!",
    },
    "fields": [
        {
            "name": "",
            "value": ""
        },
        {
            "name": "",
            "value": ":arrows_counterclockwise:"
        }
    ]
}
reply_embed = discord.Embed().from_dict(reply_embed_json)

reset_embed_json = {
    "title": "Conversation has been reset",
    "description": "Replies: 0\nYour name: \nLLaMA's name: \nPrompt: ",
    "color": 39129,
    "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
    "url": "https://github.com/xNul/chat-llama-discord-bot",
    "footer": {
        "text": "Contribute to ChatLLaMA on GitHub!"
    }
}
reset_embed = discord.Embed().from_dict(reset_embed_json)

status_embed_json = {
    "title": "Status",
    "description": "You don't have a job queued.",
    "color": 39129,
    "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
    "url": "https://github.com/xNul/chat-llama-discord-bot",
    "footer": {
        "text": "Contribute to ChatLLaMA on GitHub!"
    }
}
status_embed = discord.Embed().from_dict(status_embed_json)

# Load text-generation-webui
# Define functions
def get_model_specific_settings(model):
    settings = shared.model_config
    model_settings = {}

    for pat in settings:
        if re.match(pat.lower(), model.lower()):
            for k in settings[pat]:
                model_settings[k] = settings[pat][k]

    return model_settings

def list_model_elements():
    elements = ["cpu_memory", "auto_devices", "disk", "cpu", "bf16", "load_in_8bit", "trust_remote_code", "load_in_4bit", "compute_dtype", "quant_type", "use_double_quant", "wbits", "groupsize", "model_type", "pre_layer", "autogptq", "triton", "desc_act", "threads", "n_batch", "no_mmap", "mlock", "n_gpu_layers", "n_ctx", "llama_cpp_seed"]
    for i in range(torch.cuda.device_count()):
        elements.append(f"gpu_memory_{i}")

    return elements

def load_preset_values(preset_menu, state, return_dict=False):
    generate_params = {
        "do_sample": True,
        "temperature": 1,
        "top_p": 1,
        "typical_p": 1,
        "epsilon_cutoff": 0,
        "eta_cutoff": 0,
        "tfs": 1,
        "top_a": 0,
        "repetition_penalty": 1,
        "encoder_repetition_penalty": 1,
        "top_k": 0,
        "num_beams": 1,
        "penalty_alpha": 0,
        "min_length": 0,
        "length_penalty": 1,
        "no_repeat_ngram_size": 0,
        "early_stopping": False,
        "mirostat_mode": 0,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1
    }
    

# Configuration Handling
# This part of the code loads configuration settings from a YAML file.

    with open(Path(f"presets/{preset_menu}.yaml"), "r") as infile:
        preset = yaml.safe_load(infile)

    for k in preset:
        generate_params[k] = preset[k]
    
    generate_params["temperature"] = min(1.99, generate_params["temperature"])
    if return_dict:
        return generate_params
    else:
        state.update(generate_params)
        return state, *[generate_params[k] for k in ["do_sample", "temperature", "top_p", "typical_p", "epsilon_cutoff", "eta_cutoff", "repetition_penalty", "encoder_repetition_penalty", "top_k", "min_length", "no_repeat_ngram_size", "num_beams", "penalty_alpha", "length_penalty", "early_stopping", "mirostat_mode", "mirostat_tau", "mirostat_eta"]]

# Update the command-line arguments based on the interface values
def update_model_parameters(state, initial=False):
    elements = list_model_elements()  # the names of the parameters
    gpu_memories = []

    for i, element in enumerate(elements):
        if element not in state:
            continue

        value = state[element]
        if element.startswith("gpu_memory"):
            gpu_memories.append(value)
            continue

        if initial and vars(shared.args)[element] != vars(shared.args_defaults)[element]:
            continue

        # Setting null defaults
        if element in ["wbits", "groupsize", "model_type"] and value == "None":
            value = vars(shared.args_defaults)[element]
        elif element in ["cpu_memory"] and value == 0:
            value = vars(shared.args_defaults)[element]

        # Making some simple conversions
        if element in ["wbits", "groupsize", "pre_layer"]:
            value = int(value)
        elif element == "cpu_memory" and value is not None:
            value = f"{value}MiB"

        if element in ["pre_layer"]:
            value = [value] if value > 0 else None

        setattr(shared.args, element, value)

    found_positive = False
    for i in gpu_memories:
        if i > 0:
            found_positive = True
            break

    if not (initial and vars(shared.args)["gpu_memory"] != vars(shared.args_defaults)["gpu_memory"]):
        if found_positive:
            shared.args.gpu_memory = [f"{i}MiB" for i in gpu_memories]
        else:
            shared.args.gpu_memory = None

# Loading custom settings
settings_file = None
if shared.args.settings is not None and Path(shared.args.settings).exists():
    settings_file = Path(shared.args.settings)
elif Path("settings.yaml").exists():
    settings_file = Path("settings.yaml")
elif Path("settings.json").exists():
    settings_file = Path("settings.json")

if settings_file is not None:


# Setup Logging with Different Levels
import logging

logging.basicConfig(level=logging.INFO)  # Change this to DEBUG, WARNING, ERROR, or CRITICAL as needed

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)  # Change this to DEBUG, WARNING, ERROR, or CRITICAL as needed

# Example usages of different logging levels
logger.debug("This is a debug message.")
logger.info("This is an info message.")
logger.warning("This is a warning message.")
logger.error("This is an error message.")
logger.critical("This is a critical message.")



# Packaging and Deployment
# To deploy this bot, you can package it using Docker or other containerization tools.
# You can also deploy it directly to a server or use a cloud service like AWS, Azure, or Heroku.

# Dockerfile example:
# ---------------------
# FROM python:3.9
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# CMD ["python", "your_bot_script.py"]

# Deployment commands example:
# ----------------------------
# Build Docker image: docker build -t your_bot_image .
# Run Docker container: docker run your_bot_image
