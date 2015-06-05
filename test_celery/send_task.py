# coding: utf-8

# $Id: $


from test_celery.app import sample_task

sample_task.apply_async()