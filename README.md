<div align="center">
  <h1>🚀 Kubernetes StatefulSet Architecture Demo</h1>
  <p><i>A production-grade, containerized Nginx deployment designed to showcase the power of Stateful workloads, Dynamic Provisioning, and RBAC in Kubernetes.</i></p>
</div>

---

## 📌 Project Overview

This repository demonstrates the fundamental difference between standard stateless apps (like typical website frontends) and **Stateful** applications (like databases). 

By exploring this lab, you'll understand why StatefulSets exist and how they guarantee network identity, ordered deployment, and sticky persistent storage for mission-critical applications.

---

## 🏗️ Architecture Explanations

Here are the core pillars powering this deployment:

> **Why a StatefulSet instead of a Deployment?**  
> 🔹 **Stable Network Identity:** StatefulSets provide each pod with a predictable, persistent host name (e.g., `nginx-statefulset-0`). While Deployments treat all pods interchangeably, StatefulSets treat each pod as a unique entity (Pets vs. Cattle).  
> 🔹 **Persistent Storage:** Each pod in a StatefulSet is bound to its own PersistentVolume. If a pod crashes and is rescheduled, it automatically reattaches the same exact disk, ensuring data persistence!

> **How PVC works with StatefulSet**  
> We use a `volumeClaimTemplates` field to dynamically generate a unique PersistentVolumeClaim (PVC) for each pod replica. If you scale this app to 5 replicas, Kubernetes will automatically generate 5 independent storage disks!

> **Why use a Headless Service?**  
> Configured by setting `clusterIP: None`, this service avoids distributing and load-balancing traffic. Instead, when queried via DNS, it returns the exact, individual IP addresses of the backend pods. This is how clustered databases know how to talk directly to each other!

> **Securing with RBAC**  
> **Role-Based Access Control (RBAC)** limits what the Pods can do inside the cluster. We bind this app to a restricted `ServiceAccount` with permissions *only* to `get` and `list` pods in its specific namespace. If the container gets hacked, the attacker cannot steal cluster secrets.

---

## ⚡ Deployment Instructions

Ready to launch? Run these commands to apply the YAML manifests in order:

```bash
# 1. Create the Namespace
kubectl apply -f k8s/nginx-stateful/01-namespace.yaml

# 2. Create the StorageClass
kubectl apply -f k8s/nginx-stateful/02-storageclass.yaml

# 3. Apply Security & Role-Based Access (RBAC)
kubectl apply -f k8s/nginx-stateful/04-serviceaccount.yaml
kubectl apply -f k8s/nginx-stateful/05-role.yaml
kubectl apply -f k8s/nginx-stateful/06-rolebinding.yaml

# 4. Create the Services
kubectl apply -f k8s/nginx-stateful/07-headless-service.yaml
kubectl apply -f k8s/nginx-stateful/09-service.yaml

# 5. Launch the StatefulSet
kubectl apply -f k8s/nginx-stateful/08-statefulset.yaml
```

---

## 🎮 Interactive Demonstration Guide

This section is designed to visually demonstrate the core features of Stateful applications on Kubernetes! Try running these live experiments:

### 🔍 Step 1: Predictable Network Identity
Run this command to view the running pods:
```bash
kubectl get pods -n demo-app
```
💡 **Key Concept:** Notice the name of the pod: `nginx-statefulset-0`. If a standard Deployment was used, this would be a random hash like `nginx-75f8b9-x2z`. StatefulSets assign strict indexes (0, 1, 2) which are critical for databases.

### 💾 Step 2: Dynamic Provisioning (Storage)
Run this command to explore the persistent disks:
```bash
kubectl get pvc,pv -n demo-app
```
💡 **Key Concept:** You did not manually create a disk in Google Cloud! This perfectly illustrates Dynamic Provisioning in action. Because we used a `volumeClaimTemplate`, Kubernetes automatically talked to GKE and provisioned it for you!

### 🔥 Step 3: Proving Data Persistence
This is the most impactful experiment. We will intentionally kill the pod to prove that both the data and identity survive.

1️⃣ **Verify the data:** (Our initialization container placed an HTML file here)
```bash
kubectl exec -it nginx-statefulset-0 -n demo-app -- cat /usr/share/nginx/html/index.html
```
*(You will see: `<h1>Initialization successful!</h1>`)*

2️⃣ **Forcefully delete the pod!**
```bash
kubectl delete pod nginx-statefulset-0 -n demo-app
```

3️⃣ **Immediately watch the pod recreate:**
```bash
kubectl get pods -n demo-app -w
```
💡 **Key Concept:** Notice the pod comes back with the EXACT same name, and automatically re-attaches itself to the EXACT same Persistent Volume. If you check the data again, the data is perfectly intact! 

### 🛡️ Step 4: Testing Security (Least Privilege)
What happens if an attacker compromises our Nginx container? Can they steal cluster secrets?

Execute a test as the application's Service Account to see if it can list pods:
```bash
kubectl auth can-i list pods --as=system:serviceaccount:demo-app:nginx-sa -n demo-app
```
*(Output: yes ✅)*

Execute a test to see if it can delete or view secrets:
```bash
kubectl auth can-i delete secrets --as=system:serviceaccount:demo-app:nginx-sa -n demo-app
```
*(Output: no ❌)*

💡 **Key Concept:** Because we bound a specific `Role`, this pod is securely containerized. If compromised, the attacker is trapped with severely limited visibility, safeguarding your cluster.
