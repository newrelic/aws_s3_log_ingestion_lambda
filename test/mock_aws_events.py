import json
import os

def create_mock_aws_event(file_name="mock.json"):
    with open(os.path.join("test", "mock_event_files", file_name)) as json_file:
        return json.load(json_file)