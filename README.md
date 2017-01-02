# AWSCrossRegionReplicationLambda

Use this script at your own risk. Note that it deleted snapshots from the target region based on retentions settings. To try this out create an AWS Lambda Function, setup the mandatory environment variables and hit Test. Example:

SOURCE_REGION = 'us-east-1'
TARGET_REGION = 'us-west-1'
TEST_ENV_TAG_TO_REPLICATE=tag:scheduler:ebs-snapshot:test
PROD_ENV_TAG_TO_REPLICATE=tag:scheduler:ebs-snapshot:prod
TEST_ENV_RETENTION_DAYS=7
PROD_ENV_RETENTION_DAYS=2555

# More Info
For more info see http://thinkinginsoftware.blogspot.com/2016/12/aws-ec2-dr-cross-region-replication-for.html
