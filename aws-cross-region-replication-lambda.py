# aws-cross-region-replication-lambda.py
# @author: Nestor Urquiza
# @date: 20161226
# @description: Cross Region replication script. Use at your own risk!
# Customize this lambda using environment variables

import boto3
import botocore
from pprint import pprint
import os
from datetime import datetime
from datetime import timedelta

# Environment specific constants
SOURCE_REGION=os.environ["SOURCE_REGION"]
TARGET_REGION=os.environ["TARGET_REGION"]
TEST_ENV_TAG_TO_REPLICATE=os.environ["TEST_ENV_TAG_TO_REPLICATE"]
PROD_ENV_TAG_TO_REPLICATE=os.environ["PROD_ENV_TAG_TO_REPLICATE"]
TEST_ENV_RETENTION_DAYS=int(os.environ["TEST_ENV_RETENTION_DAYS"])
PROD_ENV_RETENTION_DAYS=int(os.environ["PROD_ENV_RETENTION_DAYS"])

# Define clients for the two regions
source_ec2 = boto3.client('ec2', region_name=SOURCE_REGION)
target_ec2 = boto3.client('ec2', region_name=TARGET_REGION)

# Define resources
source_resource = boto3.resource('ec2', region_name=SOURCE_REGION)

def lambda_handler(event, context):
    # Define what specific instance tags should be scanned for replication
    # If test and production instances are tagged for in-region-backups (BCP)
    # Then the same tags can be used for cross region replication (DR)
    reservations_test = source_ec2.describe_instances(
        Filters=[
            {'Name': TEST_ENV_TAG_TO_REPLICATE, 'Values': ['true']},
        ]
    ).get(
        'Reservations', []
    )
    reservations_prod = source_ec2.describe_instances(
        Filters=[
            {'Name': PROD_ENV_TAG_TO_REPLICATE, 'Values': ['true']},
        ]
    ).get(
        'Reservations', []
    )
    
    reservations = reservations_test + reservations_prod
    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    # A list of replicated snapshots will be printed
    print "Replicated:"
    print "InstanceName\tInstanceId\tVolumeName\tVolumeId\tSnapshotId\tSnapshotState"
    for instance in instances:
        instance_id = instance['InstanceId']
        try:
            instance_name = [
            str(t.get('Value')) for t in instance['Tags']
            if t['Key'] == 'Name'][0]
        except IndexError:
            instance_name = 'None'

        # Find volumes in used by qualified for replication instances
        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            volume_id = dev['Ebs']['VolumeId']
            # Get the volume name
            volume = source_ec2.describe_volumes(
                Filters = [
                    {
                        'Name': 'volume-id',
                        'Values': [
                            volume_id,
                        ]
                    }
                ]
            )['Volumes'][0]
            try:
                volume_name = [
                str(t.get('Value')) for t in volume['Tags']
                if t['Key'] == 'Name'][0]
            except IndexError:
                volume_name = 'None'

            # Find the snapshots for the volume
            source_snapshots = source_ec2.describe_snapshots(
                Filters = [
                    {
                        'Name': 'volume-id',
                        'Values': [
                            volume_id,
                        ]
                    }
                ]
            )['Snapshots']

            for snapshot in source_snapshots:
                snapshot_id = snapshot['SnapshotId']
                snapshot_state = snapshot['State']
                tz_info = snapshot['StartTime'].tzinfo
                # Snapshots that were not taken within the last 24 hours do not qualify for replication
                if snapshot['StartTime'] > datetime.now(tz_info) + timedelta(days=-1):     
                    # Snapshots that are not completed do not qualify for replication
                    if(snapshot_state != 'completed'):
                        continue
                    snapshot_description = instance_name + ':' + volume_name + ':' + snapshot_id

                    # Guarantee that source snapshots are named after their volume (should be removed if that is already the case)
                    snapshot_resource = source_resource.Snapshot(snapshot_id)
                    snapshot_resource.create_tags(
                        Tags = [
                            {
                                'Key': 'Name',
                                'Value': volume_name
                            },
                        ]
                    )
    
                    # Find any target snapshot that is already a replica
                    target_snapshots = target_ec2.describe_snapshots(
                        Filters = [
                            {
                                'Name': 'description',
                                'Values': [
                                    snapshot_description,
                                ]
                            }
                        ]
                    )['Snapshots']
                        
                    # Replicate only those snapshots that were not replicated before
                    if not target_snapshots:
                        try:
                            target_ec2.copy_snapshot(
                                SourceRegion=SOURCE_REGION,
                                SourceSnapshotId=snapshot_id,
                                Description=snapshot_description,
                                DestinationRegion=TARGET_REGION
                            )
                            print '%s\t%s\t%s\t%s\t%s\t%s' % (
                                instance_name, instance_id, volume_name, volume_id, snapshot_id, snapshot_state)
                        except botocore.exceptions.ClientError as e:
                            print e

    # Delete the target snapshots depending on retention policy
    test_target_snapshots = target_ec2.describe_snapshots(
        Filters = [
            {
                'Name': TEST_ENV_TAG_TO_REPLICATE,
                'Values': ['true']
            }
        ]
    )['Snapshots']
    prod_target_snapshots = target_ec2.describe_snapshots(
        Filters = [
            {
                'Name': PROD_ENV_TAG_TO_REPLICATE,
                'Values': ['true']
            }
        ]
    )['Snapshots']
    for snapshot in test_target_snapshots:
        tz_info = snapshot['StartTime'].tzinfo
        if snapshot['StartTime'] < datetime.now(tz_info) + timedelta(days=-TEST_ENV_RETENTION_DAYS):
            snapshot_id = snapshot['SnapshotId']
            target_ec2.delete_snapshot(
                SnapshotId = snapshot_id
            )
            print "Snapshot %s deleted from %s" % (
                snapshot_id, TARGET_REGION)
    for snapshot in prod_target_snapshots:
        tz_info = snapshot['StartTime'].tzinfo
        if snapshot['StartTime'] < datetime.now() + timedelta(days=-PROD_ENV_RETENTION_DAYS):
            snapshot_id = snapshot['SnapshotId']
            target_ec2.delete_snapshot(
                SnapshotId = snapshot_id
            )
            print "Snapshot %s deleted from %s" % (
                snapshot_id, TARGET_REGION)
