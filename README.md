[![Community Project header](https://github.com/newrelic/open-source-office/raw/master/examples/categories/images/Community_Project.png)](https://github.com/newrelic/open-source-office/blob/master/examples/categories/index.md#community-project)



# s3-log-ingestion-lambda

>AWS Serverless Application that sends log data from S3 to New Relic Logging.

## Pre-requisites

>To forward data to New Relic you'll need access to your license key. You can access your license key by following the steps listed here: [New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key).

>You will also need to configure your AWS credentials so that they are accessible from your local terminal: [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

> Max log file size in the s3 bucket is 150 MB uncompressed. Max supported individual log line size is 0.25 MB. Data beyond these limits will not get processed. 

> Take advantage of New Relic's log parsing capabilities by specifying the log type as an environment variable for the lambda. Pick from the set of "logtype" listed: [Built-in parsing rulesets](https://docs.newrelic.com/docs/logs/new-relic-logs/ui-data/new-relic-logs-parsing-built-rules-custom-parsing#built-in-rules)



## Installation

### Configure Lambda from AWS Severless Application Repository (SAR)

> 1. Find "NewRelic-log-ingestion-s3" on the SAR (you have to check the "Show apps that create custom IAM roles or resource policies" box)
> 2. Under "Application Settings" add your New Relic license key
> 3. (Optional) Under "Application Settings" add your "LOG_TYPE" 
> 4. Acknowledge that this app creates custom IAM roles and press the "Deploy" button
> 5. Wait for the "resources" to be created
> 6. Navigate to AWS Lambda and open the functions
> 7. Find "NewRelic-log-ingestion-s3" in the list and click on the function name
> 8. Click on "Add Trigger" and select the "S3" trigger
> 9. Configure your "Bucket" with the bucket name of where you are logging to. 
> 10. Configure "EventType" to "all object create events"
> 11. (Optional) configure "prefix" and "suffix"
> 12. Select "enable trigger" and click "Add"
> 13. Congratulations your Lambda is successfully set up!
> 14. To test your lambda setup:
     1. Upload a new log file to your s3 bucket
    2. Go to New Relic Logs and view your test logs


### Configure Lambda Using Serverless

Follow these steps below to deploy the log ingestion function manually. 

1. Clone this repository: `git clone <REPO>`
2. Install Serverless: `npm install -g serverless`
3. Install the serverless-python-requirements plugin: `npm install`
4. If not running Linux, [install Docker](https://docs.docker.com/install/) and keep it running
5. [Retrieve your New Relic License Key](https://docs.newrelic.com/docs/accounts/install-new-relic/account-setup/license-key)
6. Set the LICENSE_KEY environment variable: `export LICENSE_KEY=your-license-key-here`
7. Set the SERVICE_NAME environment variable: `export SERVICE_NAME=your-service-name-here`
8. Set the S3_BUCKET_NAME environment variable: `export S3_BUCKET_NAME=your-s3-bucket-name`
9. [Optional] You can send logs from a specific location in the bucket only. Set the S3_Prefix (subdirectory name) `export S3_PREFIX=your-s3-subdirectory-name`
10. [Optional] Set the LOG_TYPE (subdirectory name) `export LOG_TYPE=your-log-type-here`
11. Deploy the function: `serverless deploy`
 


## Support

New Relic hosts and moderates an online forum where customers can interact with New Relic employees as well as other customers to get help and share best practices. Like all official New Relic open source projects, there's a related Community topic in the New Relic Explorers Hub. You can find this project's topic/threads here:

>Add the url for the support thread here

## Contributing
Full details about how to contribute to
Contributions to improve s3-log-ingestion-lambda are encouraged! Keep in mind when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.
To execute our corporate CLA, which is required if your contribution is on behalf of a company, or if you have any questions, please drop us an email at opensource@newrelic.com.

## License
s3-log-ingestion-lambda is licensed under the [Apache 2.0](http://apache.org/licenses/LICENSE-2.0.txt) License.
> The s3-log-ingestion-lambda also uses source code from third party libraries. Full details on which libraries are used and the terms under which they are licensed can be found in the third party notices document.

## Support
Visit the support thread on [Explorer Hub](https://discuss.newrelic.com/t/aws-s3-log-ingestion-lambda/).

## Troubleshooting FAQs

```bash:
 Error: docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
```
When using serverless to deploy the lambda from your machine, this error message may occur. This may mean either docker is not running or it has not been correctly set up. Please ensure docker is runnig on your machine when deploying the lambda using serverless.



```bash:
An error occurred when creating the trigger: Configurations overlap. Configurations on the same bucket cannot share a common event type.
```
If this error message appears while adding a Lambda "Trigger", ensure your s3 does not have another event of the same type on the bucket.
Ie, your s3 bucket cannot have multiple "all object create events" events. 


