# Multi-Tenant Kubeflow Platform on Kubernetes

## 1. Problem Statement

The goal of this project is to design and implement a **multi-tenant Kubeflow service** where multiple customers (tenants) can run machine learning pipelines independently while sharing the same Kubernetes cluster.

Example tenants:

* Customer A → Team RCB
* Customer B → Team RR

### Requirements

* Tenants must work independently
* Isolation must be ensured using namespaces
* All tenants must share the same Kubernetes cluster
* Each tenant should have its own Kubeflow pipeline

---

## 2. Solution Overview

We implemented a **multi-tenant architecture** using:

* Kubernetes as the underlying orchestration platform
* Kubeflow Pipelines for ML workflow execution
* Kubernetes namespaces for tenant isolation
* RBAC roles and resource quotas per tenant for access control and fair usage

Each tenant is assigned a dedicated namespace within a shared Kubernetes cluster, ensuring logical isolation while maintaining efficient resource utilization.

---

## 3. Repository Structure

```
kubeflow-multitenant/
├── pipelines/                 # Kubeflow pipeline definitions (Python + compiled YAML)
│   ├── rcb_pipeline.py
│   ├── rcb_pipeline.yaml
│   ├── rr_pipeline.py
│   └── rr_pipeline.yaml
├── setup/                     # Cluster and namespace bootstrap
│   ├── kind-config.yaml       # Kind cluster (control-plane + worker, Kubernetes v1.29.4)
│   └── namespaces.yaml        # Tenant namespaces: rcb, rr
├── security/                  # Per-tenant RBAC and resource quotas
│   ├── rcb-role.yaml
│   ├── rcb-rolebinding.yaml
│   ├── rr-role.yaml
│   ├── rr-rolebinding.yaml
│   ├── resource-quota-rcb.yaml
│   └── resource-quota-rr.yaml
├── requirements.txt           # Python deps (kfp 2.16.0, kubernetes, etc.)
├── .gitignore
└── readme.md
```

---

## 4. Architecture

### High-Level Architecture

```
Kubernetes Cluster (Shared)
│
├── Namespace: rcb
│   ├── RCB Pipeline
│   ├── RBAC (rcb-user → rcb-role)
│   ├── ResourceQuota (tenant-quota)
│   └── Pods (Pipeline Execution)
│
├── Namespace: rr
│   ├── RR Pipeline
│   ├── RBAC (rr-user → rr-role)
│   ├── ResourceQuota (tenant-quota)
│   └── Pods (Pipeline Execution)
│
└── Namespace: kubeflow
    ├── Kubeflow Pipelines UI
    ├── Workflow Controller
    └── Metadata & Storage Services
```

---

## 5. Key Components

### 5.1 Kubernetes

* Provides container orchestration
* Manages pods, scheduling, and resource allocation
* Enables namespace-based isolation

### 5.2 Kubeflow Pipelines

* Used to define and execute ML workflows
* Converts Python-based pipeline definitions into Kubernetes workloads
* Executes each pipeline step as a Kubernetes pod

### 5.3 Namespaces (Core of Multi-Tenancy)

* `rcb` → Customer A (Team RCB)
* `rr` → Customer B (Team RR)

Namespaces provide logical isolation, separate resource visibility, and independent execution environments.

### 5.4 RBAC

Per-tenant `Role` and `RoleBinding` manifests in `security/` grant namespace-scoped access:

| Tenant | Kubernetes user | Role        |
|--------|-----------------|-------------|
| RCB    | `rcb-user`      | `rcb-role`  |
| RR     | `rr-user`       | `rr-role`   |

Each role allows `get`, `list`, `watch`, `create`, and `delete` on `pods` and `services` within its namespace.

### 5.5 Resource Quotas

Each tenant namespace has a `ResourceQuota` (`tenant-quota`) limiting:

| Resource           | Limit   |
|--------------------|---------|
| `requests.cpu`     | 2       |
| `requests.memory`  | 2Gi     |
| `limits.cpu`       | 4       |
| `limits.memory`    | 4Gi     |

---

## 6. Pipeline Execution Flow

```
User → Kubeflow UI → Pipeline Submission
      ↓
Pipeline Compiled (Python → YAML)
      ↓
Workflow Created in Kubernetes
      ↓
Pods Scheduled in Cluster
      ↓
Execution Completed
      ↓
Logs & Results Available
```

---

## 7. Getting Started

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Kind](https://kind.sigs.k8s.io/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/)
* Python 3.x

### 1. Create the cluster

```bash
kind create cluster --config setup/kind-config.yaml
```

### 2. Apply tenant namespaces

```bash
kubectl apply -f setup/namespaces.yaml
```

### 3. Apply security policies

```bash
kubectl apply -f security/
```

### 4. Install Python dependencies and compile pipelines

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python pipelines/rcb_pipeline.py
python pipelines/rr_pipeline.py
```

This regenerates `pipelines/rcb_pipeline.yaml` and `pipelines/rr_pipeline.yaml` from the Python definitions.

### 5. Deploy Kubeflow Pipelines and run workloads

Install Kubeflow Pipelines (standalone) on the cluster, port-forward to the UI, upload the compiled YAML artifacts, and submit runs per tenant namespace.

---

## 8. Pipelines

| Pipeline       | Source                     | Compiled artifact              |
|----------------|----------------------------|--------------------------------|
| RCB pipeline   | `pipelines/rcb_pipeline.py` | `pipelines/rcb_pipeline.yaml` |
| RR pipeline    | `pipelines/rr_pipeline.py`  | `pipelines/rr_pipeline.yaml`  |

Each pipeline is a minimal KFP v2 workflow with a single component task. Recompile after editing the `.py` files:

```bash
python pipelines/rcb_pipeline.py
python pipelines/rr_pipeline.py
```

---

## 9. Multi-Tenancy Strategy

Multi-tenancy is achieved using **Kubernetes namespaces**, reinforced with **RBAC** and **resource quotas**.

### Isolation mechanism

* Each tenant operates within its own namespace
* Resources (pods, workloads) are scoped to namespaces
* RBAC restricts API access to namespace-bound principals
* Resource quotas cap CPU and memory per tenant

### Benefits

* Cost-efficient (shared cluster)
* Scalable
* Access control and usage limits beyond namespace labels alone

---

## 10. Isolation Demonstration

Verify isolation by listing pods per namespace:

```bash
kubectl get pods -n rcb
kubectl get pods -n rr
```

Check quotas and RBAC:

```bash
kubectl get resourcequota -n rcb
kubectl get resourcequota -n rr
kubectl get role,rolebinding -n rcb
kubectl get role,rolebinding -n rr
```

---

## 11. Trade-offs

### Advantages

* Efficient resource utilization on a shared cluster
* Easy to add tenants (namespace + security manifests + pipeline)
* RBAC and quotas improve fairness and access boundaries

### Limitations

* Namespace isolation is logical, not a hard security boundary
* Potential “noisy neighbor” issues remain under heavy load
* RBAC users (`rcb-user`, `rr-user`) must be wired to real auth (e.g. OIDC, client certs) in production

---

## 12. Future Enhancements

### KServe integration

* Deploy trained models as APIs
* Enable real-time inference

### GPU support

* Enable GPU-based workloads using Kubernetes device plugins
* Allow pipelines to request GPU resources

### Stronger tenancy

* NetworkPolicies for traffic isolation between namespaces
* LimitRanges and PodSecurity standards per tenant

---

## 13. Conclusion

This project demonstrates a **multi-tenant Kubeflow platform** on Kubernetes where multiple customers can share infrastructure, run independent pipelines, and operate in isolated namespaces with RBAC and resource quotas. The repository provides reproducible setup, security, and pipeline artifacts for two example tenants (RCB and RR).
