publishtimer repository
========================

This project is a service for computing publish-time-recommendations


Steps to run the project:
=========================
    1. Set working directory to base directory of the repository
    2. Append PYTHONPATH with export PYTHONPATH=${PYTHONPATH}:<PATH_OF_PARENT_DIR_OF_THIS_REPOSITORY>/publishtimer
    3. Set all the environment variables specified below
    4. To start the server enter command: 
        python publishtimer/api.py
    5. To run the unit-tests enter command:
        python test/unit_tests.py
    6. Refer docs for API methods and request params 


Environment variables required:
===============================

CROWDFIRE_INTERNAL_API_BASE_URL: Crowdfire API's base URL for getting user's access credentials

SAVE_SCHEDULE_URL: Crowdfire API's URL for writing genereated schedule

SERVICE: Crowdfire internal API's service name

CROWDFIRE_INTERNAL_API_KEY: Crowdfire API's access key

ENCRYPTION_KEY: Crowdfire API's encryption key

TWITTER_APP_KEY: Crowdfire App's Twitter consumer key

TWITTER_APP_SECRET: Crowdfire App's Twitter consumer secret

ES_HOSTS: Comma-separated list of Elasticsearch hosts 
          Format: <IP>:<PORT>, <IP>:<PORT>, ...

ES_TIMEOUT: Elasticsearch request timeout in seconds

SERVER_NAME: server on which service is to be made available (e.g.: 0.0.0.0:5001)
             Format: <HOST>:<PORT>


**Note**: 
    To set environment from a text file:
    1. Create a directory `conf` in the base directory of this repository.
    2. Create a file with name `local.env` inside this `conf` directory
    3. Specify desired values of environment variables in `conf/local.env` with one environment variable per line in following format:
            <ENVIRONMENT_VARIBLE_NAME>=<STRING_VALUE_IN_REQUIRED_FORMAT>

