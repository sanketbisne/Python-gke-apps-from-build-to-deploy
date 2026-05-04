<div align="center">
  <h1>🐍 Python GKE Application</h1>
  <p>A getting started boilerplate for deploying a Python web application on Google Kubernetes Engine (GKE) with native Google Cloud Load Balancing.</p>
</div>

---

## 🚀 Features
- **Multi-architecture Image Builds**: Explicitly configures Docker images for `linux/amd64` architecture targets, guaranteeing smooth deployment on standard GKE nodes even if built locally on an ARM-based (Apple Silicon) Macbook.
- **Native GKE Ingress**: Includes `ingress.class: gce` configuration to automatically provision and sync a Google Cloud HTTP(S) External Load Balancer without the need for manual controller installations (like NGINX).
- **Dynamic Configuration**: Safely injects configurations and sensitive data into the Python environment runtime utilizing standard Kubernetes `ConfigMap` and base64 encoded K8s `Secret` objects.

## 📂 Project Structure

```text
.
├── app.py                     # The Python Flask Application Server
├── requirements.txt           # Python application dependencies
├── Dockerfile                 # Multi-architecture container specification
└── k8s/
    ├── configmap.yaml         # Non-sensitive configuration variables
    ├── secret.yaml            # Sensitive encoded credentials
    ├── deployment.yaml        # Main K8s workload orchestration
    ├── service.yaml           # NodePort service exposing the deployment to the Ingress
    └── ingress.yaml           # Defines the public entrypoint via GKE Load Balancer
```

## 🛠️ Deploying to Kubernetes (GKE)

### 1. Authenticate to your Cluster
Make sure you authenticate to your active GKE cluster and map your `kubectl` context:
```bash
gcloud container clusters get-credentials <CLUSTER-NAME> --zone <ZONE> --project <PROJECT-ID>
```

### 2. Build and Push the Container
If you are building your image on an ARM device (e.g. Apple M1/M2/M3), you must strictly define the target architecture for standard GKE deployment. 

Use Docker `buildx` to cross-compile the AMD64 architecture target and push directly to your cluster's Google Container Registry (GCR) or Artifact Registry:
```bash
docker buildx build --platform linux/amd64 -t gcr.io/<PROJECT-ID>/python-app:latest --push .
```

*Note: Be sure to update your `k8s/deployment.yaml` file so the `image` string matches your repository's tag.*

### 3. Apply the Manifests
Push the configuration structure straight to the cluster:
```bash
kubectl apply -f k8s/
```

### 4. Wait for IP Assignment
Google Cloud will now spawn a Load Balancer for your application. This provisioning commonly takes `2-5 minutes`. 

Watch for the IP address using the following command:
```bash
kubectl get ingress python-app-ingress -w
```

## 🌐 Verifying deployment

Once the Ingress fetches an `ADDRESS`, update your system's `/etc/hosts` or your Cloud DNS platform's `A` record linking your test domain (e.g., `www.example.com`) to the yielded External IP.

Hit your endpoints to test proper resolution:
```bash
curl -H "Host: www.example.com" http://<YOUR-LOAD-BALANCER-IP>/
curl -H "Host: www.example.com" http://<YOUR-LOAD-BALANCER-IP>/about
```

---

<div align="center">
  <i>Deployed with standard Kubernetes Best Practices ✨</i>
</div>
