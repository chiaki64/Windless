#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Monitor

import os
import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.config import dev
# from utils.shortcuts import load_config

# config = load_config()
# dev = config.get('dev')


def log(s):
    print("[Monitor] %s" % s)


class MyFileSystemEventHandler(FileSystemEventHandler):
    def __init__(self, fn):
        super(MyFileSystemEventHandler, self).__init__()
        self.restart = fn

    def on_any_event(self, event):
        if event.src_path.endswith((".py", ".yaml")):
            log("Python source has changed:%s" % event.src_path)
            self.restart()


def kill_process():
    global process
    if process:
        log("Kill process %s" % process.pid)
        process.kill()
        process.wait()
        log("Process end with %s" % process.returncode)
        process = None


def start_process():
    global process, command
    log("Start process %s" % command)
    process = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


def restart_process():
    kill_process()
    start_process()


def start_watch(path):
    observer = Observer()
    observer.schedule(MyFileSystemEventHandler(restart_process), path, recursive=True)
    observer.start()
    log("Wathching directory %s" % path)
    start_process()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    if dev:
        command = ['python3', 'melody.py']
    else:
        command = ['python3', '/code/core/melody.py']

    path = os.path.abspath(".")
    start_watch(path)
