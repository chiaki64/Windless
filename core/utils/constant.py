#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.abstract import Singleton


class Const(metaclass=Singleton):
    def __init__(self):
        self.CATEGORY = []


CONST = Const()



