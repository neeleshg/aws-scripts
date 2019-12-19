'''
Description: Script to get Instance Details and RI details from all regions.
Note: This script is written in Python3

Usage:
   - export AWS_CONFIG_FILE=~/.aws/config
   - export AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials
   - python get_instance_details_profiles.py <Profile Name> <Regions separated by Commas>
     For eg. python get_instance_details_profiles.py test us-east-1,us-west-1

   OR to check in all region dont give any regions
     For eg. python get_instance_details_profiles.py test

   

  Example of AWS_CONFIG file:

  [default]
  region = us-east-1

  [profile test]
  region = us-east-1
  role_arn = SWITCH ROLE ARN
  source_profile = default

  Example of AWS_CREDENTIAL file:
  # Main Account
  [default]
  aws_access_key_id = <Access Key>
  aws_secret_access_key = <Secret Access Key>

'''


import boto3
import os
import sys
from datetime import datetime

profile_name = sys.argv[1]

aws_regions = None

if len(sys.argv) == 3:
	aws_regions = list(sys.argv[2].split(','))  ### Add regions in this list

session = boto3.Session(profile_name=profile_name)


# Function to get Instace Count per type
def get_instance_count_per_type(session,aws_region):
    ec2_client = session.client('ec2',region_name=aws_region)
    instance_type = {}
    response = ec2_client.describe_instances()
    for i in response['Reservations']:
    	if i['Instances'][0]['InstanceType'] in instance_type:
    		instance_type[i['Instances'][0]['InstanceType']] = instance_type[i['Instances'][0]['InstanceType']] + 1
    	else:
    		instance_type[i['Instances'][0]['InstanceType']] = 1
    return(instance_type)


# Get Active Reserved Instance Reservation details

def get_reserved_instance_details(session,aws_region):
	ec2_client = session.client('ec2',region_name=aws_region)
	reservedInstanceDetails = {}
	response = ec2_client.describe_reserved_instances(
		Filters=[
			{
				'Name': 'state',
				'Values': [
					'active'
				]
			}
		]
	)
	reservedInstanceList = []
	count=1
	for i in range(len(response['ReservedInstances'])):
		reservationNumber = "Reservation-{}".format(count)
		reservedInstanceList.append({reservationNumber: {"InstanceType":response['ReservedInstances'][i]['InstanceType'], \
            "InstanceCount":response['ReservedInstances'][i]['InstanceCount'], \
            "OfferingType":response['ReservedInstances'][i]['OfferingType'], \
            "OfferingClass":response['ReservedInstances'][i]['OfferingClass'], \
            "EndingOn":response['ReservedInstances'][i]['End'].strftime("%m/%d/%Y, %H:%M:%S")
	    }})

		count = count + 1

	return(reservedInstanceList)

# If AWS Region is defined, check instances for that region

if aws_regions:
	for region in aws_regions:
		print("======================= Instance Details =======================")
		instanceDetails = get_instance_count_per_type(session,region)
		if instanceDetails:
			print("{}:{}".format(region,instanceDetails))
		else:
			print("{}: No Instances running in region".format(region))

		print("======================= Reserved Instance Details =======================")
		reservedInstances = get_reserved_instance_details(session,region)
		if reservedInstances:
			for reservation in reservedInstances:
				print("{}:{}".format(region,reservation))
		else:
			print("{}: No Reserved Instances in region".format(region))

# If No Region is defined, it will check in all EC2 regions
else:
	ec2_client = session.client('ec2',region_name=session.region_name)
	all_regions = ec2_client.describe_regions()
	for record in all_regions['Regions']:
		print("======================= Instance Details =======================")
		instanceDetails = get_instance_count_per_type(session,record['RegionName'])
		if instanceDetails:
			print("{}:{}".format(record['RegionName'],instanceDetails))
		else:
			print("{}: No Instances running in region".format(record['RegionName']))

		print("======================= Reserved Instance Details =======================")
		reservedInstances = get_reserved_instance_details(session,record['RegionName'])
		if reservedInstances:
			for reservation in reservedInstances:
				print("{}:{}".format(record['RegionName'],reservation))
		else:
			print("{}: No Reserved Instances in region".format(record['RegionName']))





