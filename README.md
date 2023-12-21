[![](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=58F9TDDRBND4L)

# AWS Cross Region Replication Lambda

An AWS Lambda Function to replicate a datacenter from one live region to a different DR region.

# WARNING
Use this script at your own risk. Note that it deletes snapshots from the target region based on retentions settings. 

# Try it
To try this out create an AWS Lambda Function, setup the mandatory environment variables and hit Test. Example:

```
SOURCE_REGION = 'us-east-1'
TARGET_REGION = 'us-west-1'
TEST_ENV_TAG_TO_REPLICATE=tag:scheduler:ebs-snapshot:test
PROD_ENV_TAG_TO_REPLICATE=tag:scheduler:ebs-snapshot:prod
TEST_ENV_RETENTION_DAYS=7
PROD_ENV_RETENTION_DAYS=2555
```

# More Info
For more info see http://thinkinginsoftware.blogspot.com/2016/12/aws-ec2-dr-cross-region-replication-for.html
