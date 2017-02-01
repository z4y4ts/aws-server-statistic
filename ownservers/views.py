from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.shortcuts import render
from django.views import generic
from django.http import Http404

from .models import EC2Servers

import datetime
import requests
import boto3
import json
import re


class ServersInformation(generic.ListView):
    model = EC2Servers
    template_name = 'servers.html'

    def get_context_data(self, **kwargs):
        context = super(ServersInformation, self).get_context_data(**kwargs)

        if self.kwargs['person'] == 'boss' or self.kwargs['person'] == 'employee':
            context['person'] = self.kwargs['person']
        else:
            raise Http404

        context['servers'] = EC2Servers.objects.all()
        context['server'] = get_object_or_404(EC2Servers, instance_id=self.kwargs['server'])

        return context


class HomePage(View):
    template_name = 'homepage.html'

    def get(self, request):

        # check, how much time DB does not refresh data
        last_refresh = EC2Servers.objects.all()[0].scheduled.replace(tzinfo=None)
        current_time = datetime.datetime.now() + datetime.timedelta(hours=2)

        period = (current_time - last_refresh).seconds // 3600

        # boto3
        ec2 = boto3.resource('ec2')

        instances = [instance.id for instance in ec2.instances.all()]

        # if we deleted server in AWS-EC2, we need to delete him in DB
        for server in EC2Servers.objects.all():
                if server.instance_id not in instances:
                    EC2Servers.objects.filter(instance_id=server.instance_id).delete()

        # get all instances
        for instance_id in instances:

            ec2server = EC2Servers()
            instance = ec2.Instance(instance_id)

            volumes_cost = 0.10

            try:
                # take last updated cost
                server_cost_by_hour_api = EC2Servers.objects.all()[5].server_cost_by_hour
            except Exception:
                # take old cost, not actually old, but may be
                server_cost_by_hour_api = 0.012

            # if result is more, than hour - gonna to do it
            if EC2Servers.objects.all().count() == 0 or period is not 0:
                print('hi')
                instance_types_list = {}
                instance_types_list.update({instance.instance_id: instance.instance_type})

                region_data_and_hash = self.get_current_prices()
                regions_list = region_data_and_hash[0]
                prices_by_region = region_data_and_hash[1]

                instance_type = instance_types_list[instance.instance_id]
                region = regions_list[instance.instance_id]
                server_cost_by_hour_api = prices_by_region[region][instance_type]

            # default fields
            server_cost_by_hour = server_cost_by_hour_api

            volumes_overall_count = sum([volum.size for volum in instance.volumes.all()])
            volumes_overall_cost = volumes_cost * volumes_overall_count * 1024 * 12 / (24 * 30)
            volumes_overall_cost_formatted = float("{0:.2f}".format(volumes_overall_cost))

            server_overall_cost = (datetime.datetime.now() + datetime.timedelta(hours=2) - instance.launch_time.replace(
                tzinfo=None)).seconds // 3600 * 0.012
            monthly_cost = volumes_overall_cost + server_overall_cost

            launch_time = instance.launch_time + datetime.timedelta(hours=2)
            scheduled = datetime.datetime.now() + datetime.timedelta(hours=2)

            # if server does not exist
            if EC2Servers.objects.filter(name=instance.tags[0]['Value']).count() == 0:
                ec2server.name = instance.tags[0]['Value']
                ec2server.instance_id = instance.id
                ec2server.type = instance.instance_type
                ec2server.state = instance.state['Name']
                ec2server.public_ip_address = instance.public_ip_address
                ec2server.private_ip_address = instance.private_ip_address
                ec2server.security_group = instance.security_groups[0]['GroupId']
                ec2server.vpc_id = instance.vpc_id
                ec2server.volumes = ', '.join([volume.id for volume in instance.volumes.all()])

                ec2server.volumes_cost = volumes_overall_cost_formatted
                ec2server.server_cost_by_hour = server_cost_by_hour

                ec2server.volumes_overall_cost = monthly_cost

                ec2server.overall_cost_by_month = float("{0:.2f}".format(monthly_cost))
                ec2server.launch_time = launch_time
                ec2server.scheduled = scheduled
                ec2server.save()

            else:
                # if server exists, we have to update data about time and cost
                EC2Servers.objects.filter(name=instance.tags[0]['Value']).update(
                    name=instance.tags[0]['Value'],
                    instance_id=instance.id,
                    type=instance.instance_type,
                    state=instance.state['Name'],
                    public_ip_address=instance.public_ip_address,
                    private_ip_address=instance.private_ip_address,
                    security_group=instance.security_groups[0]['GroupId'],
                    vpc_id=instance.vpc_id,
                    volumes=', '.join([volume.id for volume in instance.volumes.all()]),
                    volumes_cost=volumes_overall_cost_formatted,
                    server_cost_by_hour=server_cost_by_hour,
                    overall_cost_by_month=float("{0:.2f}".format(monthly_cost)),
                    launch_time=launch_time,
                    scheduled=scheduled)

        # render first instance information after person choice
        basic_instance = EC2Servers.objects.get(instance_id=instances[0]).instance_id

        return render(request, self.template_name, {'basic_instance': basic_instance})

    @staticmethod
    def get_current_prices():

        client = boto3.client('ec2')

        regions = client.describe_regions()['Regions']

        all_regions = [region['RegionName'] for region in regions]
        hash_map = {}

        for region in all_regions:
            ec2 = boto3.resource('ec2', region_name=region)

            try:
                for instance in ec2.instances.all():
                    hash_map.update({instance.id: region})
            except Exception:
                pass

        url = 'http://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js'

        j = requests.get(url).text

        if 'callback(' in j:
            j = j.split('callback(')[1][:-2]

        j = re.sub(r"{\s*(\w)", r'{"\1', j)
        j = re.sub(r",\s*(\w)", r',"\1', j)
        j = re.sub(r"(\w):", r'\1":', j)

        prices_by_region = {}
        regions_list = list(set([hash_map[key] for key in hash_map]))

        for region in regions_list:
            for item in json.loads(j)['config']['regions']:
                if item['region'] == region:
                    prices_by_region[item['region']] = {}
                    for sizes in item['instanceTypes']:
                        for size in sizes['sizes']:
                            for price in size['valueColumns']:
                                prices_by_region[item['region']][size['size']] = price['prices']['USD']

        return [hash_map, prices_by_region]
