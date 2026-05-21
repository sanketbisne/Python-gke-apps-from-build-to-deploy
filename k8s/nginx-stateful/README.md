# Nginx Stateful Deployment Guide

This artifact contains explanations, deployment instructions, and verification commands for the Nginx StatefulSet deployment requested.

## 1. Overview & Explanations

### Why StatefulSet is used instead of Deployment
- **Stable Network Identity:** StatefulSets provide each pod with a predictable, persistent host name (e.g., `nginx-statefulset-0`). While Deployments treat all pods interchangeably, StatefulSets maintain the identity of each pod across restarts.
- **Ordered Deployment and Scaling:** StatefulSets deploy, scale, and terminate pods in a strict ordinal sequence. This is essential for applications like databases where primary/follower nodes must start in a specific order.
- **Persistent Storage:** Each pod in a StatefulSet is bound to its own PersistentVolume. If a pod crashes and is rescheduled, it automatically reattaches the same exact PersistentVolume, ensuring data persistence.

### How PVC works with StatefulSet
- StatefulSets use a `volumeClaimTemplates` field to dynamically generate a unique PersistentVolumeClaim (PVC) for each pod replica. 
- For example, replica 0 will get a PVC named `nginx-data-nginx-statefulset-0`, which bounds to a specific PersistentVolume. If the pod dies, the new pod spawned by the StatefulSet reattaches the existing claim and volume, retaining all previous data.

### Difference between Headless Service and Normal Service
- **Normal Service:** Maps to a single ClusterIP, acting as a load-balancer that proxies traffic randomly to the healthy backend pods.
- **Headless Service:** Configured by setting `clusterIP: None`, this service avoids distributing traffic directly. Instead, when queried via DNS, it returns the individual IP addresses of the connected backend pods. StatefulSets rely on a headless service to provide DNS records for each replica (e.g., `nginx-statefulset-0.nginx-headless.demo-app.svc.cluster.local`).

### How RBAC improves security
- **Role-Based Access Control (RBAC)** limits what Pods (via their `ServiceAccount`) can do inside the Kubernetes cluster.
- By binding our application to a restricted `ServiceAccount` and attaching a `Role` with permissions *only* to `get` and `list` pods in its specific namespace, we ensure that if our container gets compromised, the attacker cannot read secrets, delete cluster resources, or escalate privileges.

### How dynamic provisioning works in Kubernetes
- **Dynamic Provisioning** automates the creation of storage volumes. Instead of an administrator manually provisioning disk drives in the cloud provider, a developer simply requests storage (via a PVC) referencing a `StorageClass`.
- A provisioner driver (in our case the GKE `pd.csi.storage.gke.io`) listens to the API server and automatically reaches out to Google Cloud Platform to create the actual persistent disk (PD) when the claim is created, seamlessly binding it via a PersistentVolume (PV).

---

## 2. Deployment Commands

Run these to apply the created YAML manifests in order:

```bash
# Move to the directory containing manifests
cd /Users/sanketbisne/python-gke-app/k8s/nginx-stateful

# 1. Create the Namespace
kubectl apply -f 01-namespace.yaml

# 2. Create the StorageClass
kubectl apply -f 02-storageclass.yaml

# 3. Apply RBAC (ServiceAccount, Role, RoleBinding)
kubectl apply -f 04-serviceaccount.yaml
kubectl apply -f 05-role.yaml
kubectl apply -f 06-rolebinding.yaml

# 4. Create the Services (Headless & ClusterIP)
kubectl apply -f 07-headless-service.yaml
kubectl apply -f 09-service.yaml

# 5. Create the StatefulSet
kubectl apply -f 08-statefulset.yaml

# Note: The StatefulSet uses `volumeClaimTemplates` to automatically create PVCs. 
# We provided `03-pvc.yaml` if you wanted to see the standalone variant, but applying the StatefulSet is all you need!
```

---

## 3. Verification Commands

Run these commands to verify the resources were created correctly and operate as intended.

**Verify the Namespace & StorageClass:**
```bash
kubectl get ns demo-app
kubectl get sc standard-pd
```

**Verify the Pods (Wait for Running state):**
```bash
# Check pod status, you should see 'nginx-statefulset-0' since it's a StatefulSet
kubectl get pods -n demo-app -o wide -w

# Check pod logs and see Nginx starting
kubectl logs nginx-statefulset-0 -n demo-app
```

**Verify the PVC and Volumes:**
```bash
# The StatefulSet's volumeClaimTemplate automatically generates a PVC
kubectl get pvc -n demo-app

# View details about where the volume is mounted inside the pod
kubectl describe pod nginx-statefulset-0 -n demo-app | grep Mounts -A 5
```

**Verify the StatefulSet:**
```bash
# Should show 1/1 READY
kubectl get statefulset -n demo-app
```

**Verify the Services:**
```bash
# Notice the headless service has 'None' for CLUSTER-IP
kubectl get svc -n demo-app
```

**Verify RBAC Permissions:**
```bash
# Check if the service account can list pods in the namespace (Should be 'yes')
kubectl auth can-i list pods \
  --as=system:serviceaccount:demo-app:nginx-sa \
  -n demo-app

# Check if the service account can delete secrets (Should be 'no')
kubectl auth can-i delete secrets \
  --as=system:serviceaccount:demo-app:nginx-sa \
  -n demo-app
```

---

## 4. Architecture Demonstration Guide

This section is designed to visually demonstrate the core features of Stateful applications on Kubernetes, rather than simply standing up the deployment.

### 4.1 The Architecture Overview (The "Why")
Unlike standard stateless frontend applications (which use Deployments), we are building a foundation for a Stateful Application (like a database).

- **StatefulSets:** Give us predictable pod names and sticky, persistent storage.
- **Headless Services:** Give each pod its own personal DNS address instead of load balancing.
- **RBAC:** Ensures if the application is hacked, the attacker can't read our cluster secrets.

### 4.2 Interactive Demonstration Commands

#### Step 1: Predictable Network Identity
Run this command to view the running pods:
```bash
kubectl get pods -n demo-app
```
**Key Concept:** Notice the name of the pod: `nginx-statefulset-0`. If a standard Deployment was used, this would be a random hash like `nginx-75f8b9-x2z`. StatefulSets assign a strict index (0, 1, 2) which is critical for databases that require a primary/replica hierarchy.

#### Step 2: Dynamic Provisioning (Storage)
Run this command to explore the Persistent Volume Claims:
```bash
kubectl get pvc,pv -n demo-app
```
**Key Concept:** We did not manually create a disk in Google Cloud! This perfectly illustrates Dynamic Provisioning in action. Because we used a `volumeClaimTemplate` inside our StatefulSet pointing to the `standard-pd` StorageClass, Kubernetes automatically talked to GKE and provisioned a 1Gi disk for pod 0.

#### Step 3: Proving Data Persistence
This is the most impactful experiment. You will intentionally kill the pod to prove that both the data and identity survive.

**A.** First, verify that data exists in the persistent storage (our init container placed an HTML file here):
```bash
kubectl exec -it nginx-statefulset-0 -n demo-app -- cat /usr/share/nginx/html/index.html
```
*(You will see the output: `<h1>Initialization successful!</h1>`)*

**B.** Now, forcefully delete the pod!
```bash
kubectl delete pod nginx-statefulset-0 -n demo-app
```

**C.** Immediately watch the pod recreate:
```bash
kubectl get pods -n demo-app -w
```
**Key Concept:** Notice the pod comes back with the EXACT same name (`nginx-statefulset-0`), and automatically re-attaches itself to the exact same Persistent Volume. If you check the data again (by running the `kubectl exec` command from Step A), the data is perfectly intact! If this were a Deployment, the volume would likely be destroyed unless manually managed.

#### Step 4: The Headless Service
Run this command to view the exposed services:
```bash
kubectl get svc -n demo-app
```
**Key Concept:** Look at the `nginx-headless` service. Its Cluster-IP is set to `None`. While a normal service dynamically load-balances traffic, a headless service simply tells Kubernetes: 'Provide a DNS record so traffic can route directly to pod `nginx-statefulset-0` in the backend.' This is the networking mechanism clustered databases use to communicate with each other!

#### Step 5: The Principle of Least Privilege (RBAC)
Let's prove our security hardening works. What happens if an attacker compromises our Nginx container? Can they steal cluster secrets?

Execute a test as the application's Service Account to see if it can list pods:
```bash
kubectl auth can-i list pods --as=system:serviceaccount:demo-app:nginx-sa -n demo-app
```
*(Output: yes)*

Execute a test to see if it can delete or view secrets:
```bash
kubectl auth can-i delete secrets --as=system:serviceaccount:demo-app:nginx-sa -n demo-app
```
*(Output: no)*

**Key Concept:** Because we bound a specific `Role` to our `ServiceAccount`, this pod is securely containerized. If compromised, the attacker is trapped with severely limited visibility, safeguarding the rest of the cluster.

By walking through these steps, the fundamental purpose and utility of StatefulSets become incredibly clear.
