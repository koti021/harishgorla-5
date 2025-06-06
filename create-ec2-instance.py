import boto3
import os
import sys
from botocore.exceptions import ClientError

def create_key_pair(ec2, key_name):
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        print(f"Key Pair '{key_name}' already exists. Using the existing key.")
    except ClientError:
        print(f"Key Pair '{key_name}' does not exist. Creating a new one...")
        key_pair = ec2.create_key_pair(KeyName=key_name)
        with open(f"{key_name}.pem", "w") as file:
            file.write(key_pair['KeyMaterial'])
        os.chmod(f"{key_name}.pem", 0o400)
        print(f"New Key Pair created and saved as {key_name}.pem")

def get_or_create_security_group(ec2, group_input):
    security_group_id = None
    try:
        if group_input.startswith("sg-"):
            response = ec2.describe_security_groups(GroupIds=[group_input])
            security_group_id = response['SecurityGroups'][0]['GroupId']
            print(f"Security Group ID '{group_input}' found. Using the existing group.")
        else:
            response = ec2.describe_security_groups(GroupNames=[group_input])
            security_group_id = response['SecurityGroups'][0]['GroupId']
            print(f"Security Group Name '{group_input}' found. Using the existing group.")
    except ClientError:
        print(f"Security Group '{group_input}' does not exist. Creating a new one...")
        response = ec2.create_security_group(GroupName=group_input, Description="Security group for EC2 instance")
        security_group_id = response['GroupId']
        ec2.authorize_security_group_ingress(GroupId=security_group_id, IpProtocol="tcp", FromPort=22, ToPort=22, CidrIp="0.0.0.0/0")
        print(f"New Security Group created with ID: {security_group_id}")

    return security_group_id

def get_ami_id(region, ami_name="amzn2-ami-hvm-*-x86_64-gp2"):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_images(
        Filters=[
            {'Name': 'name', 'Values': [ami_name]},
            {'Name': 'state', 'Values': ['available']}
        ],
        Owners=['amazon']
    )
    if response['Images']:
        return response['Images'][0]['ImageId']
    else:
        raise Exception(f"No AMI found for {ami_name} in region {region}")

def main():
    print("""\n!!! Welcome to HINTechnologies !!!\n
This script will guide you step-by-step to create an EC2 instance.
""")

    # AWS Region
    region_options = {
        "1": "ap-south-1",
        "2": "us-east-1",
        "3": "us-west-2",
        "4": "eu-north-1",
    }
    print("Select AWS Region:")
    for key, value in region_options.items():
        print(f"{key} - {value}")
    region_choice = input("Enter the number corresponding to your desired region: ").strip()
    region = region_options.get(region_choice, "us-east-1")

    session = boto3.Session(region_name=region)
    ec2 = session.client('ec2')

    # Key Pair
    key_name = input("Enter the name of the Key Pair (if it doesn't exist, it will be created): ").strip()
    create_key_pair(ec2, key_name)

    # Security Group
    group_input = input("Enter the Security Group name or ID (if it doesn't exist, it will be created): ").strip()
    security_group_id = get_or_create_security_group(ec2, group_input)

    # Instance Type Selection
    print("Select Instance Type:")
    print("1 - [2vCPU and 2GiB RAM - t3.small] TomcatServer")
    print("2 - [2vCPU and 4GiB RAM - t3.medium] Jenkins_Server | Sonarqube | Jfrog | Docker | K8S")
    print("3 - [2vCPU and 8GiB RAM - t3.large] Kubernetes Setup")
    instance_type_choice = input("Enter the number corresponding to your desired instance type: ").strip()
    instance_type_map = {"1": "t3.small", "2": "t3.medium", "3": "t3.large"}
    instance_type = instance_type_map.get(instance_type_choice, "t3.small")
    print(f"Selected Instance Type: {instance_type}")

    # AMI ID
    ami_id = input("Enter the AMI ID (default: 'ami-0d682f26195e9ec0f'): ").strip() or "ami-0d682f26195e9ec0f"

   
        
    # Storage
    storage_size = input("Enter Storage Size in GB (default: 8): ").strip() or "8"

    # User Data
    default_user_data_file = "temp-swap-setup-file.txt"
    if os.path.isfile(default_user_data_file):
        user_data_file = default_user_data_file
    else:
        user_data_file = input("User Data file not found. Enter path to the User Data file: ").strip()
        if not os.path.isfile(user_data_file):
            print("Error: Specified User Data file does not exist.")
            sys.exit(1)
    with open(user_data_file, 'r') as file:
        user_data = file.read()

    # Instance Count and Names
    instance_count = int(input("Enter the number of instances to create (default: 1): ").strip() or "1")
    if instance_count <= 0:
        print("Instance count must be at least 1.")
        sys.exit(1)

    if instance_count > 1:
        instance_names = []
        for i in range(instance_count):
            instance_name = input(f"Enter the name for instance {i+1}: ").strip()
            if not instance_name:
                print(f"Instance name for instance {i+1} is required.")
                sys.exit(1)
            instance_names.append(instance_name)
    else:
        instance_name = input("Enter the name for the EC2 instance: ").strip()
        if not instance_name:
            print("Instance name is required.")
            sys.exit(1)
        instance_names = [instance_name]

    # Launch Instances
    block_device_mappings = [{
        "DeviceName": "/dev/xvda",
        "Ebs": {
            "VolumeSize": int(storage_size),
            "DeleteOnTermination": True,
            "VolumeType": "gp2"
        }
    }]
    print("Launching instances...")
    try:
        instances = ec2.run_instances(
            ImageId=ami_id,
            MinCount=instance_count,
            MaxCount=instance_count,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            BlockDeviceMappings=block_device_mappings,
            UserData=user_data,
        )
        instance_ids = [instance['InstanceId'] for instance in instances['Instances']]
        print(f"Successfully launched EC2 instances: {', '.join(instance_ids)}")

        # Tag Instances
        for instance_id, name in zip(instance_ids, instance_names):
            ec2.create_tags(Resources=[instance_id], Tags=[{"Key": "Name", "Value": name}])
        print("Instances tagged successfully.")

        # Fetch Instance Details
        response = ec2.describe_instances(InstanceIds=instance_ids)
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                print(f"Instance ID: {instance['InstanceId']}, Public IP: {instance.get('PublicIpAddress')}")

    except Exception as e:
        print(f"Error launching instances: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
