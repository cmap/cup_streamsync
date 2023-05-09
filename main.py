import streamsync as ss
import os
import s3fs
from metadata import prism_metadata
import json
import pandas as pd
import numpy as np
import boto3

# AWS/API setup
API_URL = 'https://api.clue.io/api/'
API_KEY = os.environ['API_KEY']
BUILDS_URL = API_URL + 'data_build_types/prism-builds'

# get list of builds
builds = prism_metadata.get_data_from_db(
    endpoint_url=BUILDS_URL,
    user_key=API_KEY,
    fields=['name']
)

fs = s3fs.S3FileSystem(anon=False)

builds_list = []
for i in builds:
    builds_list.append(list(i.values())[0])

builds_dict = {build: build for build in builds_list}
json_builds_dict = json.dumps(builds_dict)


# print(f"Available builds are {json_builds_dict}")


# This is a placeholder to get you started or refresh your memory.
# Delete it or adapt it as necessary.
# Documentation is available at https://streamsync.cloud


# Its name starts with _, so this function won't be exposed
def _update_message(state):
    is_even = state["counter"] % 2 == 0
    message = ("+Even" if is_even else "-Odd")
    state["message"] = message


def decrement(state):
    state["counter"] -= 1
    _update_message(state)


def increment(state):
    state["counter"] += 1
    # Shows in the log when the event handler is run
    print(f"The counter has been incremented.")
    _update_message(state)


def set_build(state, payload):
    # Set the state variable "build" to the selected option
    state["build"] = payload
    print(f"Selected build is {state['build']}")

    # Create dictionary of available build files
    s3 = boto3.client('s3')
    bucket = 'cup.clue.io'
    prefix = state["build"]
    print(f"Selected build is {prefix}")
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' in response:
        objects = response['Contents']
        existing_plots = [obj['Key'].split("/")[1] for obj in objects]
        print(f"Found {len(existing_plots)} objects with prefix '{prefix}' in bucket '{bucket}'")
        state["files"] = existing_plots

    _update_message(state)


def get_plots(state):
    s3 = boto3.client('s3')
    bucket = 'cup.clue.io'
    prefix = state["build"]
    files = state["files"]

    # Initialize an empty dictionary to store the plotly plots
    plots = {}

    # Iterate through the list of filenames
    for filename in files:
        # Subset to only json files
        if filename.endswith(".json"):

            # Create the file path by combining the prefix and filename
            file_key = f"{prefix}/{filename}"

            # Download the file from the S3 bucket and read its contents
            file_obj = s3.get_object(Bucket=bucket, Key=file_key)
            file_content = file_obj['Body'].read().decode('utf-8')
            plot_name = filename.split(".")[0]

            # Parse the contents as JSON and add to the plots dictionary with the filename as the key
            plot_json = json.loads(file_content)
            state[plot_name] = plot_json

    # Set the state variable "plots" to the dictionary of plots
    _update_message(state)


# Initialise the state

# "_my_private_element" won't be serialised or sent to the frontend,
# because it starts with an underscore

initial_state = ss.init_state({
    "my_app": {
        "title": "My App"
    },
    "_my_private_element": 1337,
    "message": None,
    "counter": 26,
    "build": None,
    "builds_dict": builds_dict,
    "files": None,
})

_update_message(initial_state)
