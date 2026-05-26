```markdown
# 🛡️ Self-Healing DevSecOps Platform on AWS EKS

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=for-the-badge&logo=kubernetes&logoColor=white)
![Jenkins](https://img.shields.io/badge/jenkins-%232C5263.svg?style=for-the-badge&logo=jenkins&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)
![SonarQube](https://img.shields.io/badge/SonarQube-black?style=for-the-badge&logo=sonarqube&logoColor=4E9BCD)

A robust, fully automated, end-to-end DevSecOps pipeline and self-healing cloud-native application deployed on Amazon EKS. 

This project demonstrates advanced cloud infrastructure management, featuring zero-trust security integrations, automated Helm rollbacks, Terraform drift detection, and secure IAM Role for Service Accounts (IRSA) integration with Amazon RDS. The core application is a Python-based "Cloud-Native Visitor Book" designed with high availability and automated resilience in mind.

## 🚀 Key Features

* **Self-Healing Architecture:** Automated monitoring via Jenkins pipelines that detects Pod failures (`CrashLoopBackOff`, `ImagePullBackOff`) and automatically triggers a `helm rollback` to the last stable state.
* **Infrastructure Drift Detection:** Automated `terraform plan` integrated into CI/CD that detects unauthorized infrastructure changes and automatically recovers/re-applies the baseline configuration.
* **Comprehensive Security Gates (DevSecOps):** * **GitLeaks:** Pre-deployment scanning for hardcoded secrets.
    * **SonarQube:** Static Application Security Testing (SAST) and code quality checks.
    * **Trivy:** Vulnerability scanning across the local file system, Docker images, and Kubernetes YAML manifests.
    * **Cosign:** Cryptographic signing of Docker images to guarantee artifact integrity.
    * **Kyverno:** Kubernetes admission controller enforcing container security (disallowing `latest` tags, preventing privileged root access, and enforcing resource limits).
* **Passwordless Database Authentication:** Secure connection between EKS and Amazon RDS using AWS IAM Authentication (IRSA/OIDC), completely eliminating hardcoded database credentials via Boto3 auth tokens.
* **Dynamic Monitoring & Alerting:** Full Prometheus and Grafana stack with Alertmanager configured to trigger email webhooks on critical pod failures.
* **Helm Package Management:** Dynamic Kubernetes deployments utilizing `values.yaml` for flexible environment configuration.

## 🏗️ Architecture & Tech Stack

* **Cloud Provider:** Amazon Web Services (EKS, EC2, RDS, VPC, IAM, OIDC)
* **Container Orchestration:** Kubernetes (EKS v1.30), Helm
* **CI/CD & Automation:** Jenkins (Shared Libraries, Declarative Pipelines), Terraform (IaC)
* **Security (DevSecOps):** GitLeaks, SonarQube, Trivy, Cosign, Kyverno
* **Monitoring & Observability:** Prometheus (Kube-Prometheus-Stack), Grafana, Alertmanager
* **Application Layer:** Python 3.12 (Flask), PyMySQL, Boto3, Docker (Multi-stage builds)

## 📋 Prerequisites

Before deploying this platform, ensure you have the following installed and configured:

* **AWS CLI** (v2.x) configured with necessary access.
* **eksctl** and **kubectl** installed locally.
* **Helm v3** installed for package management.
* **Docker** installed and running.
* A running **Jenkins Server** with necessary plugins.
* **Terraform** installed for infrastructure provisioning.

## 🛠️ Getting Started / Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/yashmane108/Self-Healing-DevSecOps-Platform-on-AWS-EKS.git](https://github.com/yashmane108/Self-Healing-DevSecOps-Platform-on-AWS-EKS.git)
cd Self-Healing-DevSecOps-Platform-on-AWS-EKS

```

### 2. Provision the EKS Cluster

Use the provided configuration to spin up a managed EKS cluster with `eksctl`.

```bash
eksctl create cluster -f k8s/cluster.yaml

```

*(Note: This process provisions the VPC, Subnets, Internet Gateways, EKS Control Plane, and Worker Nodes and takes approx. 15-20 minutes).*

### 3. Enable OIDC & Configure IAM for RDS (IRSA)

Enable the OIDC provider to allow EKS service accounts to assume IAM roles for passwordless RDS access.

```bash
eksctl utils associate-iam-oidc-provider \
    --region=us-east-1 \
    --cluster=devops-project-eks \
    --approve

```

Apply the IAM policy and bind it to the Kubernetes Service Account using `eksctl create iamserviceaccount`.

### 4. Deploy Kubernetes Policies (Kyverno)

Apply cluster policies to ensure zero-trust standards before deploying the application.

```bash
kubectl apply -f k8s/kyverno-policy.yaml

```

### 5. Deploy the Application via Helm

Deploy the application dynamically using the provided Helm chart.

```bash
helm upgrade --install my-app ./my-chart \
    --namespace my-ns \
    --create-namespace 

```

## 🔄 Deployment & CI/CD Pipeline

The project utilizes a highly declarative `Jenkinsfile` divided into distinct automated stages:

1. **Source & Scan:** Clones the repository, scans for secrets (`GitLeaks`), and validates code quality (`SonarQube`).
2. **Containerize & Validate:** Builds a multi-stage Docker image, runs `Trivy` vulnerability scans on files/images/K8s manifests, and pushes to Docker Hub.
3. **Sign & Secure:** Cryptographically signs the container image using `Cosign` to prevent supply chain attacks.
4. **Infrastructure Validation:** Runs Terraform drift detection (`terraform plan -detailed-exitcode`); automatically executes `terraform apply` if unauthorized manual changes are detected in AWS.
5. **Deploy & Heal:** Deploys the application using Helm. A post-deployment health check monitors for `CrashLoopBackOff` or `ImagePullBackOff`. If detected, Jenkins automatically executes a `helm rollback` to prevent downtime.

## 📈 Monitoring Configuration

Deploy the Prometheus & Grafana stack into your cluster for full observability:

```bash
kubectl create namespace monitoring
helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
helm install prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring

```

Access Grafana via port-forwarding on port `3000`. Alertmanager is pre-configured to send alerts based on pod health queries (e.g., `sum(kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}) > 0`).

## 📬 Contact / Author

**Yash Mane**

* GitHub: [@yashmane108](https://github.com/yashmane108)

```

```
