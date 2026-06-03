# This file will be used to create a workflow that takes as input: a list of pubsub messages. 
# Then it copies the file path from the pubsub message, loads the file from GCS and creates a new file in GCS. 
# Lastly, it will acknowledge the message.


import json
from time import sleep
from google.cloud import pubsub_v1, storage

PROJECT_ID = "ringtonechanger-494218"
SUBSCRIPTION_ID = "ringtone-pubsub-upload-message"

subscriber = pubsub_v1.SubscriberClient()
storage_client = storage.Client()

subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

response = subscriber.pull(
    request={
        "subscription": subscription_path,
        "max_messages": 1,
    }
)

if not response.received_messages:
    print("No messages available")
    raise SystemExit(0)

received = response.received_messages[0]
message = received.message

# GCS bucket notifications usually put bucket/object info in attributes
attrs = dict(message.attributes)
bucket_name = attrs["bucketId"]
input_path = attrs["objectId"] # This is the path to the file in GCS, e.g., "uploads/file.txt"

if not input_path.startswith("uploads/"):
    print(f"Unexpected object path: {input_path}")
    subscriber.acknowledge(
        request={
            "subscription": subscription_path,
            "ack_ids": [received.ack_id],
        }
    )   
    raise SystemExit(1)

bucket = storage_client.bucket(bucket_name)
input_blob = bucket.blob(input_path)

output_name = f"output/{input_path.split('/')[-1]}"
output_blob = bucket.blob(output_name)

local_input = "/tmp/input_file"
input_blob.download_to_filename(local_input)

# Do your processing here
sleep(5)  # Simulate processing time
output_blob.upload_from_filename(local_input)


# Only ack after successful processing
subscriber.acknowledge(
    request={
        "subscription": subscription_path,
        "ack_ids": [received.ack_id],
    }
)

print(f"Processed and acknowledged gs://{bucket_name}/{output_name}")