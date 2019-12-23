'''
Description: Script to get Instance Details and RI details from all regions.
Note: This script is written in Python3

Usage:
   - export AWS_CONFIG_FILE=~/.aws/config
   - export AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials
   - python get_instance_details_profiles.py <Profile Name> <Regions separated by Commas>
	 For eg. python get_instance_details_profiles.py test us-east-1,us-west-1

If you dont give any region, it will give an error.

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
import csv



aws_regions = None

if len(sys.argv) == 3:
	aws_regions   = list(sys.argv[2].split(','))  ### Add regions in this list
	profile_names = list(sys.argv[1].split(','))  ## Add Profiles in the list

# Function to get Instace Count per type
def get_instance_count_per_type(session,aws_region):
	print("Getting Instance Details")
	ec2_client = session.client('ec2',region_name=aws_region)
	instance_type = {}
	response = ec2_client.describe_instances()
	for i in response['Reservations']:
		if i['Instances'][0]['InstanceType'] in instance_type:
			instance_type[i['Instances'][0]['InstanceType']] = instance_type[i['Instances'][0]['InstanceType']] + 1
		else:
			instance_type[i['Instances'][0]['InstanceType']] = 1

	instance_type = str(instance_type).replace("{","").replace("}", "")
	return(instance_type)


# Get Active Reserved Instance Reservation details

def get_reserved_instance_details(session,aws_region):
	print("Getting Reserved Instance Details")
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
		reservedInstanceList.append( {"InstanceType":response['ReservedInstances'][i]['InstanceType'], \
			"InstanceCount":response['ReservedInstances'][i]['InstanceCount'], \
			"OfferingType":response['ReservedInstances'][i]['OfferingType'], \
			"OfferingClass":response['ReservedInstances'][i]['OfferingClass'], \
			"EndingOn":response['ReservedInstances'][i]['End'].strftime("%m/%d/%Y, %H:%M:%S")
		})

		count = count + 1

	return(reservedInstanceList)


# Write CSV Header
def write_csv_header(csv_file,csv_columns):
	print("Writing CSV Header")
	with open(csv_file, 'w') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
		writer.writeheader()

# Function to write CSV file
def write_csv(csv_file,csv_columns,dict_data):
	print("Writing CSV data")
	with open(csv_file, 'a') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
		writer.writerow(dict_data)

# If AWS Region is defined, check instances for that region

def getDetails(session,profile,aws_regions=None):
	# If aws_regions are defined
	if aws_regions:
		csv_instances_filenames = []
		csv_reserved_instances_filenames = []
		for region in aws_regions:
			print("\n======================================\nProfile: {} |||| Region: {}\n".format(profile,region))
			csv_instances_filenames.append("/tmp/instances-{}-{}.csv".format(profile,region))
			csv_reserved_instances_filenames.append("/tmp/reserved-instances-{}-{}.csv".format(profile,region))
			os.system('touch /tmp/instances-{}-{}.csv'.format(profile,region))
			os.system('touch /tmp/reserved-instances-{}-{}.csv'.format(profile,region))

			# Instances
			instanceDetails = get_instance_count_per_type(session,region)
			if instanceDetails:
				data = "{{'region':'{}',{}}}".format(region,instanceDetails)
				# Converted data to dict format
				data = eval(data)
				csv_file = "/tmp/instances-{}-{}.csv".format(profile,region)
				csv_columns = data.keys()
				write_csv_header(csv_file,csv_columns)
				write_csv(csv_file,csv_columns,data)
			else:
				print("No Instances found in {} and region {}".format(profile,region))
				for file in csv_instances_filenames:
					os.remove(file)
					csv_instances_filenames.remove(file)

			# Reserved Instances
			reservedInstances = get_reserved_instance_details(session,region)
			if reservedInstances:
				csv_columns = ["region","InstanceType","InstanceCount","OfferingType","OfferingClass","EndingOn"]
				csv_file = "/tmp/reserved-instances-{}-{}.csv".format(profile,region)
				write_csv_header(csv_file,csv_columns)
				for reservation in reservedInstances:
					reservation = str(reservation).replace("{","").replace("}", "")
					data = "{{'region':'{}',{}}}".format(region,reservation)
					data = eval(data)
					write_csv(csv_file,csv_columns,data)
			else:
				print("No Reserved Instances found in {} and region {}".format(profile,region))
				for file in csv_reserved_instances_filenames:
					os.remove(file)
					csv_reserved_instances_filenames.remove(file)

			# Remove CSV files in single and size is 0
			if csv_instances_filenames:
				for file in csv_instances_filenames:
					if os.stat(file).st_size == 0:
						os.remove(file)
						csv_instances_filenames.remove(file)
	
				# Create a Single Instance CSV file of instance details
				if len(csv_instances_filenames) > 1:
					for i in range(csv_instances_filenames[1:]):
						os.system('cat {} >> {}'.format(csv_instances_filenames[i+1],csv_instances_filenames[0]))
						os.remove(csv_instances_filenames[i+1])
					os.rename(csv_instances_filenames[0],"/tmp/instance-details-{}.csv".format(profile))
					print("------------------------------------")
					print("Get Instance details for {} in --> /tmp/instance-details-{}.csv".format(profile,profile))
				elif len(csv_instances_filenames) == 1:
					os.rename(csv_instances_filenames[0],"/tmp/instance-details-{}.csv".format(profile))
					print("------------------------------------")
					print("Get Instance details for {} in --> /tmp/instance-details-{}.csv".format(profile,profile))

			if csv_reserved_instances_filenames:
				for file in csv_reserved_instances_filenames:
					if os.stat(file).st_size == 0:
							print("Removing File --> {}".format(file))
							os.remove(file)
							csv_reserved_instances_filenames.remove(file)
	
				# Create a Single Instance CSV file of Reserved instance details
				if len(csv_reserved_instances_filenames) > 1:
					for i in range(csv_reserved_instances_filenames[1:]):
						os.system('cat {} >> {}'.format(csv_reserved_instances_filenames[i+1],csv_reserved_instances_filenames[0]))
						os.remove(csv_reserved_instances_filenames[i+1])
					os.rename(csv_reserved_instances_filenames[0],"/tmp/reserved-instance-details-{}.csv".format(profile))
					print("------------------------------------")
					print("Get Reserved Instance details for {} in --> /tmp/reserved-instance-details-{}.csv".format(profile,profile))
				elif len(csv_reserved_instances_filenames) == 1:
					os.rename(csv_reserved_instances_filenames[0],"/tmp/reserved-instance-details-{}.csv".format(profile))
					print("------------------------------------")
					print("Get Reserved Instance details for {} in --> /tmp/reserved-instance-details-{}.csv".format(profile,profile))

			# Empting Lists
			csv_instances_filenames = []
			csv_reserved_instances_filenames = []

	# If No Region is defined, it will check in all EC2 regions
	else:
		print('Error:Please Specify Region')


# Actual execution
for profile in profile_names:
	session = boto3.Session(profile_name=profile)
	getDetails(session,profile,aws_regions)
