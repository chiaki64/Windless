#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 数据监控

import os
import platform
import psutil


class Monitor:
    def __init__(self):
        self.system, self.release = self.system_info()

    def system_info(self):
        data = platform.uname()
        return data.system, data.release
    def cpu_info(self):
        f = open('/proc/stat')
        lines = f.readlines()
        f.close()

        for line in lines:
            line = line.lstrip()
            counters = line.split()
            if len(counters) < 5:
                continue
            if counters[0].startswith('cpu'):
                break

        total = 0
        for i in range(1, len(counters)):
            total = total + int(counters[i])
        idle = int(counters[4])
        print(total, idle)
    def sysinfo(self):
        pass


obj = Monitor()
obj.cpu_info()

