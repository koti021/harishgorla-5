import boto3
import time

def list_ec2_instances():
    # Create a session using your AWS credentials
    ec2 = boto3.client('ec2')

    try:
        # Retrieve a list of EC2 instances
        print("Fetching EC2 instances...")
        response = ec2.describe_instances()
        
        # Loop through the instances and collect their details
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Skip terminated instances
                if instance['State']['Name'] == 'terminated':
                    continue

                instance_name = "No Name"
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                
                instance_state = instance['State']['Name']
                
                instances.append({
                    'InstanceName': instance_name,
                    'State': instance_state,
                    'InstanceId': instance['InstanceId']
                })
        
        # If no instances are found
        if not instances:
            print("No EC2 instances found.")
            return None
        
        # Display the instances with name and state
        print("\nList of EC2 Instances:")
        for idx, instance in enumerate(instances):
            print(f"{idx + 1}. Name: {instance['InstanceName']}, State: {instance['State']}")
        
        return instances

    except Exception as e:
        print(f"Error fetching EC2 instances: {e}")
        return None

def stop_ec2_instances(instance_ids, instances):
    # Create a session using your AWS credentials
    ec2 = boto3.client('ec2')

    try:
        # Stop the EC2 instances
        print(f"\nAttempting to stop EC2 instances: {', '.join(instance_ids)}...")
        response = ec2.stop_instances(InstanceIds=instance_ids)

        # Output the state change of the instances after stopping
        print("\nShutdown initiated for the following EC2 Instances:")
        for instance in response['StoppingInstances']:
            instance_id = instance['InstanceId']
            current_state = instance['CurrentState']['Name']
            instance_name = next(inst['InstanceName'] for inst in instances if inst['InstanceId'] == instance_id)
            print(f"- Name: {instance_name}, State: {current_state}")

        print("\nWaiting for instances to stop...")
        
        # Poll the instance status until they are stopped
        stopped_instances = []
        while len(stopped_instances) < len(instance_ids):
            time.sleep(10)  # Check every 10 seconds
            
            # Describe the instances to check their current state
            status = ec2.describe_instances(InstanceIds=instance_ids)
            
            # Collect the instance statuses
            for reservation in status['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'stopped':
                        instance_name = next(inst['InstanceName'] for inst in instances if inst['InstanceId'] == instance['InstanceId'])
                        stopped_instances.append(instance['InstanceId'])
                        print(f"- Name: {instance_name}, State: stopped")
        
        print("\nAll selected instances have been stopped.")

    except Exception as e:
        print(f"Error stopping EC2 instances: {e}")

def start_ec2_instances(instance_ids, instances):
    # Create a session using your AWS credentials
    ec2 = boto3.client('ec2')

    try:
        # Start the EC2 instances
        print(f"\nAttempting to start EC2 instances: {', '.join(instance_ids)}...")
        response = ec2.start_instances(InstanceIds=instance_ids)

        # Output the state change of the instances after starting
        print("\nStart initiated for the following EC2 Instances:")
        for instance in response['StartingInstances']:
            instance_id = instance['InstanceId']
            current_state = instance['CurrentState']['Name']
            instance_name = next(inst['InstanceName'] for inst in instances if inst['InstanceId'] == instance_id)
            print(f"- Name: {instance_name}, State: {current_state}")

        print("\nWaiting for instances to start...")
        
        # Poll the instance status until they are running
        running_instances = []
        while len(running_instances) < len(instance_ids):
            time.sleep(10)  # Check every 10 seconds
            
            # Describe the instances to check their current state
            status = ec2.describe_instances(InstanceIds=instance_ids)
            
            # Collect the instance statuses
            for reservation in status['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        instance_name = next(inst['InstanceName'] for inst in instances if inst['InstanceId'] == instance['InstanceId'])
                        running_instances.append(instance['InstanceId'])
                        print(f"- Name: {instance_name}, State: running")
        
        print("\nAll selected instances have been started.")

    except Exception as e:
        print(f"Error starting EC2 instances: {e}")

if __name__ == "__main__":
    # List EC2 instances
    instances = list_ec2_instances()
    
    if instances:
        # Ask user what action they want to perform (stop or start)
        user_input = input("\nDo you want to stop running EC2 instances, start stopped EC2 instances, or stop all running instances? (stop/start/stop all): ").strip().lower()
        
        if user_input == 'stop':
            # Filter out running instances
            running_instances = [instance for instance in instances if instance['State'] == 'running']
            
            if running_instances:
                # Ask user which instances to stop
                print("\nThe following running instances are available to stop:")
                for idx, instance in enumerate(running_instances, 1):
                    print(f"{idx}. Name: {instance['InstanceName']}, State: {instance['State']}")
                
                selected_instances = input("\nEnter the numbers of the EC2 instances you want to stop, separated by commas (e.g., 1, 3, 5): ")
                selected_indexes = [int(i.strip()) - 1 for i in selected_instances.split(',')]

                # Ensure all entered indices are valid and within the list bounds
                if all(0 <= idx < len(running_instances) for idx in selected_indexes):
                    instance_ids_to_stop = [running_instances[idx]['InstanceId'] for idx in selected_indexes]
                    print(f"\nYou selected the following instances to stop:")
                    for idx in selected_indexes:
                        print(f"- Name: {running_instances[idx]['InstanceName']}, State: {running_instances[idx]['State']}")
                    stop_ec2_instances(instance_ids_to_stop, instances)
                else:
                    print("Invalid selection. Please ensure the numbers are within the list of running instances.")
            else:
                print("No running instances found to stop.")
        
        elif user_input == 'start':
            # Filter out stopped instances
            stopped_instances = [instance for instance in instances if instance['State'] == 'stopped']
            
            if stopped_instances:
                # Ask user which instances to start
                print("\nThe following stopped instances are available to start:")
                for idx, instance in enumerate(stopped_instances, 1):
                    print(f"{idx}. Name: {instance['InstanceName']}, State: {instance['State']}")
                
                selected_instances = input("\nEnter the numbers of the EC2 instances you want to start, separated by commas (e.g., 1, 3, 5): ")
                selected_indexes = [int(i.strip()) - 1 for i in selected_instances.split(',')]

                # Ensure all entered indices are valid and within the list bounds
                if all(0 <= idx < len(stopped_instances) for idx in selected_indexes):
                    instance_ids_to_start = [stopped_instances[idx]['InstanceId'] for idx in selected_indexes]
                    print(f"\nYou selected the following instances to start:")
                    for idx in selected_indexes:
                        print(f"- Name: {stopped_instances[idx]['InstanceName']}, State: {stopped_instances[idx]['State']}")
                    start_ec2_instances(instance_ids_to_start, instances)
                else:
                    print("Invalid selection. Please ensure the numbers are within the list of stopped instances.")
            else:
                print("No stopped instances found to start.")
        
        elif user_input == 'stop all':
            # Stop all running instances
            running_instances = [instance for instance in instances if instance['State'] == 'running']
            if running_instances:
                instance_ids_to_stop = [instance['InstanceId'] for instance in running_instances]
                print(f"\nStopping all running instances:")
                for instance in running_instances:
                    print(f"- Name: {instance['InstanceName']}, State: {instance['State']}")
                stop_ec2_instances(instance_ids_to_stop, instances)
            else:
                print("No running instances found to stop.")
        
        else:
            print("Invalid input. Please enter 'stop', 'start', or 'stop all'.")
