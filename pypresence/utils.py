"""Util functions that are needed but messy."""
import asyncio
import json
import os
import sys
import tempfile
import time

from typing import Tuple, List, Optional
from .exceptions import PyPresenceException


# Made by https://github.com/LewdNeko ;^)
def remove_none(d: dict):
    for item in d.copy():
        if isinstance(d[item], dict):
            if len(d[item]):
                d[item] = remove_none(d[item])
            if not len(d[item]):
                del d[item]
        elif d[item] is None:
            del d[item]
    return d


def _get_probable_discord_path() -> Tuple[Optional[str], List[str]]:
    """
    Gets the probable locations for the Discord IPC to be located at.

    Returns: Tuple with a possible pipe paths and a list of Discord ipc folder names
    """
    if sys.platform in ('linux', 'darwin'):
        folder_names = ['.', 'snap.discord', 'app/com.discordapp.Discord', 'app/com.discordapp.DiscordCanary']

        xdg_runtime_dir = os.environ.get('XDG_RUNTIME_DIR') # Runtime dir set by GUI environment
        if xdg_runtime_dir:
            return xdg_runtime_dir, folder_names

        users_runtime_dir = f"/run/user/{os.getuid()}" # Possible location for user's runtime
        if os.path.exists(users_runtime_dir):
            # Runtime directory check as fix for #216
            return users_runtime_dir, folder_names

        return tempfile.gettempdir(), folder_names

    elif sys.platform == 'win32':
        return r'\\?\pipe', ['.']

    return None, [] # No known Discord locations for used OS. Probably never gets here


# Returns on first IPC pipe matching Discord's
def get_ipc_path(pipe=None):
    ipc = 'discord-ipc-'
    if pipe:
        ipc = f"{ipc}{pipe}"

    tmp_dir, folder_names = _get_probable_discord_path()
    if tmp_dir is None or len(folder_names) == 0:
        return

    for folder in folder_names:
        full_path = os.path.abspath(os.path.join(tmp_dir, folder))

        if not (sys.platform == 'win32' or os.path.isdir(full_path)):
            continue

        for entry in os.scandir(full_path):
            if entry.name.startswith(ipc) and os.path.exists(entry):
                return entry.path


def get_event_loop(force_fresh=False):
    if sys.platform in ('linux', 'darwin'):
        if force_fresh:
            return asyncio.new_event_loop()
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.new_event_loop()
        if loop.is_closed():
            return asyncio.new_event_loop()
        return loop
    elif sys.platform == 'win32':
        if force_fresh:
            return asyncio.ProactorEventLoop()
        loop = asyncio.get_event_loop()
        if isinstance(loop, asyncio.ProactorEventLoop) and not loop.is_closed():
            return loop
        return asyncio.ProactorEventLoop()


# This code used to do something. I don't know what, though.
try:  # Thanks, Rapptz :^)
    create_task = asyncio.ensure_future
except AttributeError:
    create_task = getattr(asyncio, "async")
    # No longer crashes Python 3.7
