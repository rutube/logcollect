# coding: utf-8

# $Id: $
from logging import getLogger
from django.core.management import BaseCommand


class Command(BaseCommand):
    def execute(self, *args, **options):
        getLogger('test_logger').info("DJANGO")