@echo off
SetLocal EnableDelayedExpansion

@rem Check if unzip utility is available and install it if not
where /q unzip
if errorlevel 1 (
    echo Unzip utility not found. Attempting to install it via Chocolatey.
    choco install unzip -y
    where /q unzip
    if errorlevel 1 (
        echo Error: Unzip utility still not found. Please install it manually.
        exit /b 1
    )
)

@rem Install not found
if not exist "ChatLLaMA" (
    mkdir ChatLLaMA
    cd ChatLLaMA

    @rem Downloads and extracts both the Discord bot and webui files
    call curl -L https://github.com/xNul/chat-llama-discord-bot/archive/refs/heads/main.zip --output chat-llama-discord-bot-main.zip
    call curl -L https://github.com/oobabooga/text-generation-webui/releases/download/installers/oobabooga_windows.zip --output oobabooga_windows.zip
    powershell -command "Expand-Archive -Force 'chat-llama-discord-bot-main.zip' '.'"
    powershell -command "Expand-Archive -Force 'oobabooga_windows.zip' '.'"

    @rem Installs webui and tricks it into not automatically running
    set OOBABOOGA_FLAGS=--fkdlsja ^>nul 2^>^&1
    call oobabooga_windows\start_windows.bat
    cd ..

    @rem Activates the installed Miniconda environment for webui and installs the Discord bot library
    call "oobabooga_windows\installer_files\conda\condabin\conda.bat" activate "oobabooga_windows\installer_files\env"
    call python -m pip install discord

    @rem Changes webui to the latest commit ChatLLaMA supports
    cd oobabooga_windows\text-generation-webui
    call git checkout 19f78684e6d32d43cd5ce3ae82d6f2216421b9ae
    cd ..\..

    @rem Tricks webui into starting its model downloader
    set OOBABOOGA_FLAGS=--fkdlsja ^>nul 2^>^&1 ^& python download-model.py
    call oobabooga_windows\start_windows.bat
    cd ..

    @rem Moves ChatLLaMA's files to webui's directory for usage
    move "chat-llama-discord-bot-main\bot.py" "oobabooga_windows\text-generation-webui"

    echo.
    echo.
    echo.
    echo.
    echo.
    echo Installation has completed. Configuring the bot...
    echo.

    @rem Obtains the user's Discord bot token and saves it to the disk for ease of use
    set /p token="Enter your Discord bot's token: "

    cd ..
    echo !token! > token.cfg
)

@rem Loads your Discord bot token
set /p token=<token.cfg

@rem Sets webui flags to trick webui into opening the bot instead
set CHATLLAMA_FLAGS= 
set OOBABOOGA_FLAGS=--fkdlsja ^>nul 2^>^&1 ^& python bot.py --token %token% --chat --model-menu %CHATLLAMA_FLAGS%

@rem Runs the Discord bot
call ChatLLaMA\oobabooga_windows\start_windows.bat
