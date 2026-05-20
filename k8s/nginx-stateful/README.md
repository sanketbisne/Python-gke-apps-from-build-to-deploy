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
