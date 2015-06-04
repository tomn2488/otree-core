#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from lib2to3 import refactor

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.conf import settings


# =============================================================================
# CONSTANTS
# =============================================================================

CHECK = settings.PY_2TO3.get("check", ())

EXCLUDE = list(settings.PY_2TO3.get("exclude", ()))


# =============================================================================
# REFACTOR
# =============================================================================

class TestRefactorTool(refactor.RefactoringTool):

    def __init__(self, *args, **kwargs):
        self.messages = []

        # This silence all grammar logger.info
        rlogger = logging.getLogger()
        original_log_level = rlogger.level
        rlogger.setLevel(logging.ERROR)

        super(TestRefactorTool, self).__init__(*args, **kwargs)

        # restore the root logger
        rlogger.setLevel(original_log_level)

    def log_stream(self, msg, *args):
        if args:
            msg = msg % args
        self.messages.append(msg)

    def summarize(self):
        original_log_message = self.log_message
        try:
            setattr(self, "log_message", self.log_stream)
            super(TestRefactorTool, self).summarize()
        finally:
            if original_log_message:
                delattr(self, "log_message")
        self.messages.pop(0)

    def get_report(self):
        if self.messages:
            report = "\n".join(
                ["The next files are not Python 3 compatible"] +
                self.messages + ["Please check with '2to3' command"]
            )
        else:
            report = ""
        return report


# =============================================================================
# TEST
# =============================================================================

class TestStyle(TestCase):

    def setUp(self):
        fixer_names = sorted(
            set(refactor.get_fixers_from_package("lib2to3.fixes"))
        )
        self.rt = TestRefactorTool(fixer_names)
        self.check_paths = []

        for path in CHECK:
            if not os.path.isdir(path) and not os.path.isfile(path):
                msg = "'{}' is not file and is not dir".format(path)
                raise ImproperlyConfigured(msg)
            self.check_paths.append(path)

    def test_2to3(self):
        if not self.rt.errors:
            self.rt.refactor(self.check_paths)
        self.rt.summarize()

        if self.rt.messages:
            self.fail(self.rt.get_report())
