#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitor

import os
import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from components.eternity import config
from components.logger import logger
from utils.period import todate


class Handler(FileSystemEventHandler):
    def __init__(self, fn):
        super(Handler, self).__init__()
        self.restart = fn

    def on_any_event(self, event):
        if event.src_path.endswith(('.py', '.yaml')):
            self.restart()


def kill():
    global process
    if process:
        process.kill()
        process.wait()
        process = None


def start():
    global process, command
    process = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


def restart():
    kill()
    logger.warn(
        f"[{todate(int(time.time()), '%d/%b/%Y:%H:%M:%S +0800')}]::Status(Restarting Server)")

    start()


def watch(path):
    observer = Observer()
    observer.schedule(Handler(restart), path, recursive=True)
    observer.start()
    start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    command = ['python3']
    if config.dev:
        command.append('melody.py')
    else:
        command.append('/code/core/melody.py')

    path = os.path.abspath('.')
    watch(path)