#!/bin/bash

# Install not found
if [ ! -e "ChatLLaMA" ]; then
    mkdir ChatLLaMA
    cd ChatLLaMA

    # Downloads the Discord bot and webui files
    curl -L https://github.com/xNul/chat-llama-discord-bot/archive/refs/heads/main.zip --output chat-llama-discord-bot-main.zip
    curl -L https://github.com/oobabooga/text-generation-webui/releases/download/installers/oobabooga_linux.zip --output oobabooga_linux.zip

    # Checks for unzip command and installs if not available
    if ! command -v unzip &> /dev/null; then
        if command -v apt &> /dev/null; then
            echo "Installing the unzip package..."
            sudo apt update && sudo apt install -y unzip
        elif command -v yum &> /dev/null; then
            echo "Installing the unzip package..."
            sudo yum install -y unzip
        else
            echo "Error: Unsupported package manager. Please install unzip manually."
            exit 1
        fi
    fi

    # Extracts the Discord bot and webui files
    unzip chat-llama-discord-bot-main.zip
    unzip oobabooga_linux.zip

    # Installs webui and tricks it into not automatically running
    export OOBABOOGA_FLAGS="--fkdlsja >/dev/null 2>&1"
    bash oobabooga_linux/start_linux.sh

    # Activates the installed Miniconda environment for webui and installs the Discord bot library
    source "oobabooga_linux/installer_files/conda/etc/profile.d/conda.sh"
    conda activate "$(pwd)/oobabooga_linux/installer_files/env"
    python -m pip install discord

    # Changes webui to the latest commit ChatLLaMA supports
    cd oobabooga_linux/text-generation-webui
    git checkout 19f78684e6d32d43cd5ce3ae82d6f2216421b9ae
    cd ../..

    # Tricks webui into starting its model downloader
    export OOBABOOGA_FLAGS="--fkdlsja >/dev/null 2>&1; python download-model.py"
    bash oobabooga_linux/start_linux.sh

    # Moves ChatLLaMA's files to webui's directory for usage
    mv chat-llama-discord-bot-main/bot.py oobabooga_linux/text-generation-webui

    echo
    echo
    echo
    echo
    echo
    echo "Installation has completed. Configuring the bot..."
    echo

    # Obtains the user's Discord bot token and saves it to the disk for ease of use
    read -p "Enter your Discord bot's token: " token

    cd ..
    echo $token > token.cfg
fi

# Loads your Discord bot token
token=$(<token.cfg)

# Sets webui flags to trick webui into opening the bot instead
CHATLLAMA_FLAGS=""
export OOBABOOGA_FLAGS="--fkdlsja >/dev/null 2>&1; python bot.py --token $token --chat --model-menu $CHATLLAMA_FLAGS"

# Runs the Discord bot
bash ChatLLaMA/oobabooga_linux/start_linux.sh
