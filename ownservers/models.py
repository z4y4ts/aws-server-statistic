from __future__ import unicode_literals
from django.db import models

from datetime import datetime, timedelta


def current_date():
    return datetime.now() + timedelta(hours=2)


class EC2Servers(models.Model):
    name = models.CharField(max_length=250)
    instance_id = models.CharField(max_length=250)
    type = models.CharField(max_length=250)
    state = models.CharField(max_length=250)
    public_ip_address = models.CharField(max_length=250, null=True)
    private_ip_address = models.CharField(max_length=250, null=True)
    vpc_id = models.CharField(max_length=250)
    security_group = models.CharField(max_length=250)
    volumes = models.CharField(max_length=250)

    server_cost_by_hour = models.FloatField(default=0)
    volumes_cost = models.FloatField(default=0)
    overall_cost_by_month = models.FloatField(default=0)
    launch_time = models.DateTimeField(default=current_date, blank=True)
    scheduled = models.DateTimeField(default=current_date, blank=True)

    def __str__(self):
        return self.name
