publishtimer Repository
========================

This project is a service for computing publish-time-recommendations

Environment variables required:

ACCESS_DETAILS_URL: Crowdfire API's URL for getting access token

SAVE_SCHEDULE_URL: Crowdfire API's URL for writing genereated schedule

SERVICE: Crowdfire API's service name

API_KEY: Crowdfire API's access key

ENCRYPTION_KEY: Crowdfire API's encryption key

CALCULATION_QUEUE_NAME: SQS queue name to read authUids from 

TWITTER_APP_KEY: Crowdfire App's Twitter consumer key

TWITTER_APP_SECRET: Crowdfire App's Twitter consumer secret

AWS_ACCESS_KEY_ID: Crowdfire's AWS access key

AWS_SECRET_ACCESS_KEY: Crowdfire's AWS access secret

ES_HOST: Elasticsearch Host <IP>:<PORT>

ES_TIMEOUT: Elasticsearch request timeout in seconds