# Deploying the model to Google Kubernetes Engine

Let us start by creating a cluster. My cluster required 3 CPU nodes to balance monitoring and background Kubernetes tasks (3 CPU nodes that re always on is expensive for a hoobby pproject), so I will create the clusters when needed and delete them. Following is a set of instructions to create the cluster. It will be created as a zonal cluster in europe-west1-c, as it is possible to rent cheap GPUs in this zone.
```bash
gcloud container clusters create ringtone-cluster \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --zone europe-west1-c \
  --machine-type e2-medium
```
Then we also need to create a worker node with access to the GCS bucket
```bash
gcloud container node-pools create ringtone-cpu-pool \
  --cluster=ringtone-cluster \
  --zone=europe-west1-c \
  --machine-type=e2-medium \
  --enable-autoscaling \
  --min-nodes 0 \
  --max-nodes 1 \
  --num-nodes 1 \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --node-taints=workload=ringtone:NoSchedule
```

Now let us set up a pubsub notification that registers every time a file is uploaded to the GCS Bucket we created for our contacts
```bash
# 1. Create topic
gcloud pubsub topics create ringtone-pubsub

# 2. Create pull subscription
gcloud pubsub subscriptions create ringtone-pubsub-upload-message \
  --topic=ringtone-pubsub \
  --ack-deadline=300 # This is how long pubsub will wait before releasing the message. Set this to be equal to the time it will take you to process the message.

# 3. Connect bucket upload events to Pub/Sub topic - it listens to entire bucket so we have to check later if the message comes from bucket/uploads/ or from bucket/output/. Alternatively we need to create seperate buckets...
gcloud storage buckets notifications create gs://contact-info-bucket \
  --topic=ringtone-pubsub \
  --event-types=OBJECT_FINALIZE

# 4. Verify that the bucket has only the notification you created (and it is not sending duplicate messages)
gcloud storage buckets notifications list gs://contact-info-bucket

# 5. Test the notification
echo "hello" > test.txt
gcloud storage cp test.txt gs://contact-info-bucket/uploads/tester/test.txt

gcloud pubsub subscriptions pull ringtone-pubsub-upload-message \
  --auto-ack \
  --limit=10 \
  --format "table[all-box](MESSAGE_ID, ATTRIBUTES, ACK_STATUS)"
```

### Create one pod per Pub/Sub message



If you want GKE to create a pod whenever your bucket notification lands in Pub/Sub, use KEDA to watch the pubsub messages and scale the pods, depending on the traffic. To do this, install KEDA and allow it to view your pubsub messages. The installation is done via HELM (https://helm.sh/docs/intro/install)
```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --create-namespace --namespace keda

# Give KEDA the rights to view the pubsub messages
gcloud projects add-iam-policy-binding projects/ringtonechanger-494218 \
  --role roles/monitoring.viewer \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/keda/sa/keda-operator

# Create IAM for the SA account that runs the jobs. This SA needs to acknowledge the messages and view+create files in GCS.
gcloud projects add-iam-policy-binding projects/ringtonechanger-494218 \
  --role=roles/pubsub.subscriber \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/default/sa/ringtone-worker

gcloud projects add-iam-policy-binding projects/ringtonechanger-494218 \
  --role=roles/storage.objectAdmin \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/default/sa/ringtone-worker

```

Then apply the pubsub-scaler manifest and the sleeper pod job
```bash
kubectl apply -f k8s/pubsub-scaler.yaml
```

Test that pods are created when messages arrive

```bash
# 1. create messages in bubsub
for i in $(seq 1 30); do
  gcloud storage cp test.txt "gs://contact-info-bucket/uploads/tester/test_${i}.txt"
done

# 2. inspect whether jobs+pods are created
kubectl logs -n keda deployment/keda-operator
kubectl get jobs
```

# Delete if unused
```bash
# Delete the cluster
gcloud container clusters delete ringtone-cluster \
  --zone=europe-west1-c

# Delete Pub/Sub subscription and topic
gcloud pubsub subscriptions delete ringtone-pubsub-upload-message
gcloud pubsub topics delete ringtone-pubsub

# Remove GCS bucket notification
gcloud storage buckets notifications list gs://contact-info-bucket
# Then use the notification ID from the list:
gcloud storage buckets notifications delete projects/ringtonechanger-494218/buckets/contact-info-bucket/notificationConfigs/__IDENTIFICATION_ID__

# Remove IAM bindings
gcloud projects remove-iam-policy-binding projects/ringtonechanger-494218 \
  --role=roles/monitoring.viewer \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/keda/sa/keda-operator

gcloud projects remove-iam-policy-binding projects/ringtonechanger-494218 \
  --role=roles/pubsub.subscriber \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/default/sa/ringtone-worker

gcloud projects remove-iam-policy-binding projects/ringtonechanger-494218 \
  --role=roles/storage.objectAdmin \
  --member=principal://iam.googleapis.com/projects/996521322298/locations/global/workloadIdentityPools/ringtonechanger-494218.svc.id.goog/subject/ns/default/sa/ringtone-worker
```