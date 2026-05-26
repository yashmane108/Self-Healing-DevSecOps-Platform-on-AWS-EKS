Install docker and add current login user

```
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -aG docker $USER
newgrp docker
docker ps
```
java

```
sudo apt update
sudo apt install fontconfig openjdk-21-jre
java -version 
```
Jenkins

```
sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install jenkins
```
add 8080 port in ec2 instance with 0.0.0.0/0 in source 

get password:

```
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```
add shared lib, Cred in jenkins dashboard(if you want)



add jenkins user in docker group and refresh docker group

```
sudo usermod -aG docker jenkins
newgrp docker
```
install kind

```
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.31.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
kind version
```
install kubectl

```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
kubectl version --client
```
install ingress controller after cluster create else show error

```
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
```
```
sudo apt install mysql-server
```
---



RDS:

create RDS from aws console. set pass auth, create subnet gr(same vpc which ec2 has), create separate security gr for rds where add ec2 sg in source.

test from ec2 

```
mysql -h <database-endpoint> -P 3306 -u admin -p
```
dockerfile:

```python
# --- Stage 1: Build Stage ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install compiler tools needed to build certain Python packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
# Install dependencies into a local folder (wheels)
RUN pip install --no-cache-dir -r requirements.txt --target=/build/deps

# --- Stage 2: Final Runtime Stage ---
FROM python:3.12-slim

WORKDIR /app

# while use AWS RDS IAM Authenticatio
# RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/* 

# Copy only the installed Python packages from the builder stage
COPY --from=builder /build/deps /app/deps

# Copy your application files
COPY app.py .

# uncommint this wehn use AWS IAM Auth
# COPY global-bundle.pem .
# Ensure your index.html is copied if your app.py references it externally
# COPY index.html .

# Ensure Python can find installed libraries
ENV PYTHONPATH=/app/deps

EXPOSE 80

CMD ["python", "app.py"]
```


create kind cluster with extraPortMaping, kubeadmConfigPatches for ingress controller

Run this to create cluster. at last of cmd that is path where kind-config.yaml place

```
kind create cluster --name devops --config  /home/ubuntu/simple-web/k8s/kind-config.yaml
```
kind-config.yaml

```
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
# Add the workers here:
- role: worker
- role: worker
```
---

PROBLEM 1

In case ingress controller run on worker and if you want to change to control-plane then run this 

```
kubectl patch deployment ingress-nginx-controller -n ingress-nginx \
--type='json' -p='[{"op": "add", "path": "/spec/template/spec/nodeSelector", "value": {"ingress-ready": "true"}}]'
```
check where ingress-controller run on control-plane or on which worker: 

`kubectl get pods -n ingress-nginx -o wide﻿` 

---


Run this to create resources

```
kubectl apply -f app-deploy.yaml﻿
```
# app-deploy.yaml and app.py (when rds uses simple pass)
```python
from flask import Flask, render_template_string, request, redirect
import pymysql
import os
import boto3

app = Flask(__name__)

# Fetch environment variables from K8s
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME', 'devops_db')
REGION = "us-east-1"

def get_conn():


    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    ) 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Visitor Book</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; display: flex; flex-direction: column; align-items: center; }
        .header { background-color: #1a73e8; color: white; width: 100%; text-align: center; padding: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); width: 90%; max-width: 600px; margin-top: 2rem; }
        .tech-stack { background: #e8f0fe; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: left; }
        .tech-stack ul { list-style-type: none; padding: 0; margin: 0; }
        .tech-stack li { color: #1967d2; font-weight: bold; margin-bottom: 5px; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #34a853; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 1rem; }
        button:hover { background-color: #2d8e47; }
        .visitor-card { border-left: 5px solid #1a73e8; background: #fafafa; padding: 10px; margin-top: 10px; border-radius: 4px; text-align: left; }
        .status { font-weight: bold; color: {{ "green" if "✅" in db_status else "red" }}; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cloud-Native Visitor Book</h1>
    </div>
    <div class="container">
        <div class="tech-stack">
            <h3>🚀 Tech Stack Deployed:</h3>
            <ul>
                <li>🐳 Docker: Ingress-> Load Balancer, Probes, Resource: Request and Limit, Multi-Stage Dockerfile</li>
                <li>☸️ Prometheus  </li>
                <li>📊 Grafana  </li>
                <li>🤫 DevSecOps Tools: GitLeaks, SonarQube, Trivy(Install First)</li>
                <li>🤖 Jenkins: Shared Lib, Cred, Env Var, (IAM IRSA Integration)</li>
                <li>☁️ AWS: EC2, VPC, RDS (IAM Auth Enabled), EKS (Load Balancer)</li>
                
            </ul>
        </div>
        <p>Database Status: <span class="status">{{ db_status }}</span></p>
        <form method="POST">
            <input type="text" name="name" placeholder="Your Name" required>
            <textarea name="message" placeholder="Your Message" rows="3"></textarea>
            <button type="submit">Submit to RDS</button>
        </form>
        <hr>
        <h3>Recent Visitors:</h3>
        {% for entry in visitors %}
        <div class="visitor-card">
            <strong>{{ entry.name }}</strong>: {{ entry.message }} <br>
            <small style="color: #888;">{{ entry.visit_time }}</small>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/health')
def health():
    return "OK", 200

@app.route('/debug')
def debug():
    try:
        # This checks which IAM role the Pod is actually using
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return {
            "Status": "IAM Identity Found",
            "Arn": identity.get('Arn'),
            "Account": identity.get('Account')
        }
    except Exception as e:
        return {"Error": str(e)}, 500


@app.route('/', methods=['GET', 'POST'])
def index():
    db_status = "Disconnected ❌"
    visitors = []

    try:
        conn = get_conn()
        db_status = "Connected ✅"
        
        if request.method == 'POST':
            name = request.form.get('name')
            message = request.form.get('message')
            if name and message:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO visitors (name, message) VALUES (%s, %s)"
                    cursor.execute(sql, (name, message))
                conn.commit()
                conn.close() # Close before redirect
                return redirect('/')

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM visitors ORDER BY visit_time DESC")
            visitors = cursor.fetchall()
        conn.close()

    except Exception as e:
        db_status = f"Error: {str(e)} ❌"

    return render_template_string(HTML_TEMPLATE, db_status=db_status, visitors=visitors)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
```
```
apiVersion: v1
kind: Namespace

metadata:
  name: my-ns
---
apiVersion: v1
kind: Service
metadata:
  name: my-svc
  namespace: my-ns
spec:
  type: ClusterIP # add LoadBalancer
  selector:
    app: my-web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
kind: Secret
apiVersion: v1

metadata:
  name: mysql-sec
  namespace: my-ns

type: opaque
data:
stringData:  # Use stringData to put plain text; K8s will encode it for you
  password: "yourpasshere"

  host: "database-v1.cih84c6osdd0.us-east-1.rds.amazonaws.com"
  # user: "iam_user" # for IAM Auth when use Load Balancer
  user: "admin" 
  dbname: "devops_db" # Update this from 'mysql' to your new database name # Based on your 'show databases' output
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-dep
  namespace: my-ns
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-web
  template:
    metadata:
      labels:
        app: my-web
    spec:

      containers:
      - name: my-pod
        image: yashmane108/simple-app:REPLACE_ME
        securityContext:
          privileged: false
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
        imagePullPolicy: Always
        ports:
        - containerPort: 80
        # AWS RDS 
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: host
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: user
        # Pass
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: password
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: dbname
        resources:
          requests:
            memory: "64Mi"   # Guaranteed 64 Megabytes
            cpu: "100m"      # 10% of 1 CPU core
          limits:
            memory: "128Mi"  # Hard cap at 128 Megabytes
            cpu: "500m"       # Max 50% of 1 CPU core
        # --- ADD PROBES BELOW ---
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3      # Check every 15 seconds
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30  # Start checking almost immediately
          periodSeconds: 15        # Check often for traffic routing
          timeoutSeconds: 5
          failureThreshold: 3
---
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2

metadata:
  name: my-hpa
  namespace: my-ns

spec:
  scaleTargetRef:
    name: my-dep
    kind: Deployment
    apiVersion: apps/v1

  minReplicas: 1
  maxReplicas: 2

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ing
  namespace: my-ns
#  annotations:
#    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-svc
            port:
              number: 80
```
# app-deploy.yaml and app.py (when rds uses iam auth)


```python
from flask import Flask, render_template_string, request, redirect
import pymysql
import os
import boto3

app = Flask(__name__)

# Fetch environment variables from K8s
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')

DB_NAME = os.environ.get('DB_NAME', 'devops_db')
REGION = "us-east-1"

def get_conn():
    rds_client = boto3.client('rds', region_name=REGION)
    # gitleaks:allow
    token = rds_client.generate_db_auth_token(
        DBHostname=DB_HOST, 
        Port=3306, 
        DBUsername=DB_USER,
        Region=REGION
    )
    
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=token,
        database=DB_NAME,
        port=3306,
        ssl={'ca': 'global-bundle.pem'},
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    ) 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Visitor Book</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; display: flex; flex-direction: column; align-items: center; }
        .header { background-color: #1a73e8; color: white; width: 100%; text-align: center; padding: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); width: 90%; max-width: 600px; margin-top: 2rem; }
        .tech-stack { background: #e8f0fe; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: left; }
        .tech-stack ul { list-style-type: none; padding: 0; margin: 0; }
        .tech-stack li { color: #1967d2; font-weight: bold; margin-bottom: 5px; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #34a853; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 1rem; }
        button:hover { background-color: #2d8e47; }
        .visitor-card { border-left: 5px solid #1a73e8; background: #fafafa; padding: 10px; margin-top: 10px; border-radius: 4px; text-align: left; }
        .status { font-weight: bold; color: {{ "green" if "✅" in db_status else "red" }}; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cloud-Native Visitor Book</h1>
    </div>
    <div class="container">
        <div class="tech-stack">
            <h3>🚀 Tech Stack Deployed:</h3>
            <ul>
                <li>🐳 Docker: Ingress-> Load Balancer, Probes, Resource: Request and Limit, Multi-Stage Dockerfile</li>
                <li>☸️ Prometheus  </li>
                <li>📊 Grafana  </li>
                <li>🤫 DevSecOps Tools: GitLeaks, SonarQube, Trivy(Install First)</li>
                <li>🤖 Jenkins: Shared Lib, Cred, Env Var, (IAM IRSA Integration)</li>
                <li>☁️ AWS: EC2, VPC, RDS (IAM Auth Enabled), EKS (Load Balancer)</li>
                
            </ul>
        </div>
        <p>Database Status: <span class="status">{{ db_status }}</span></p>
        <form method="POST">
            <input type="text" name="name" placeholder="Your Name" required>
            <textarea name="message" placeholder="Your Message" rows="3"></textarea>
            <button type="submit">Submit to RDS</button>
        </form>
        <hr>
        <h3>Recent Visitors:</h3>
        {% for entry in visitors %}
        <div class="visitor-card">
            <strong>{{ entry.name }}</strong>: {{ entry.message }} <br>
            <small style="color: #888;">{{ entry.visit_time }}</small>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/health')
def health():
    return "OK", 200

@app.route('/debug')
def debug():
    try:
        # This checks which IAM role the Pod is actually using
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return {
            "Status": "IAM Identity Found",
            "Arn": identity.get('Arn'),
            "Account": identity.get('Account')
        }
    except Exception as e:
        return {"Error": str(e)}, 500


@app.route('/', methods=['GET', 'POST'])
def index():
    db_status = "Disconnected ❌"
    visitors = []

    try:
        conn = get_conn()
        db_status = "Connected ✅"
        
        if request.method == 'POST':
            name = request.form.get('name')
            message = request.form.get('message')
            if name and message:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO visitors (name, message) VALUES (%s, %s)"
                    cursor.execute(sql, (name, message))
                conn.commit()
                conn.close() # Close before redirect
                return redirect('/')

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM visitors ORDER BY visit_time DESC")
            visitors = cursor.fetchall()
        conn.close()

    except Exception as e:
        db_status = f"Error: {str(e)} ❌"

    return render_template_string(HTML_TEMPLATE, db_status=db_status, visitors=visitors)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
```
```
apiVersion: v1
kind: Namespace

metadata:
  name: my-ns
---
apiVersion: v1
kind: Service
metadata:
  name: my-svc
  namespace: my-ns
spec:
  type: LoadBalancer # add LoadBalancer
  selector:
    app: my-web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
kind: Secret
apiVersion: v1

metadata:
  name: mysql-sec
  namespace: my-ns

type: opaque
data:
stringData:  # Use stringData to put plain text; K8s will encode it for you
  host: "database-v1.cih84c6osdd0.us-east-1.rds.amazonaws.com"
  user: "iam_user" # for IAM Auth when use Load Balancer

  dbname: "devops_db" # Update this from 'mysql' to your new database name # Based on your 'show databases' output
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-dep
  namespace: my-ns
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-web
  template:
    metadata:
      labels:
        app: my-web
    spec:
      serviceAccountName: rds-auth-sa
      containers:
      - name: my-pod
        image: yashmane108/simple-app:REPLACE_ME
        securityContext:
          privileged: false
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
        imagePullPolicy: Always
        ports:
        - containerPort: 80
        # AWS RDS 
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: host
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: user

        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: dbname
        resources:
          requests:
            memory: "64Mi"   # Guaranteed 64 Megabytes
            cpu: "100m"      # 10% of 1 CPU core
          limits:
            memory: "128Mi"  # Hard cap at 128 Megabytes
            cpu: "500m"       # Max 50% of 1 CPU core
        # --- ADD PROBES BELOW ---
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3      # Check every 15 seconds
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30  # Start checking almost immediately
          periodSeconds: 15        # Check often for traffic routing
          timeoutSeconds: 5
          failureThreshold: 3
---
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2

metadata:
  name: my-hpa
  namespace: my-ns

spec:
  scaleTargetRef:
    name: my-dep
    kind: Deployment
    apiVersion: apps/v1

  minReplicas: 1
  maxReplicas: 2

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ing
  namespace: my-ns
#  annotations:
#    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-svc
            port:
              number: 80
```
---

# EKS
HERE WE DOING

INSTALL EKS, Login AWS, setup OIDC

## Phase 1
You need three tools on your Ubuntu EC2 to talk to EKS. Think of these as your steering wheel, pedals, and dashboard.

### Step 1: Install `eksctl` (The Cluster Creator)
This is the most important tool. It simplifies a 50-step AWS process into one command.

```
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp 
```
```
sudo mv /tmp/eksctl /usr/local/bin
```
```
eksctl version﻿ 
```
### Step 2: Update the AWS CLI
EKS requires a modern version of the AWS CLI.

1. Check your version: `aws --version` . If it’s lower than **2.x**, we should update it.
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --update
```
### Step 3: Verify your AWS Identity
Your EC2 needs to know _who_ is asking to create a cluster.

```
aws login # create IAM user and put acces key
```
```
﻿aws sts get-caller-identity 
```
create private and public key 

```
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""﻿ 
ls ~/.ssh  # (You should now see id_rsa and id_rsa.pub.)
```
output like this then only move next:

```
ubuntu@ip-172-31-43-28:~$ aws --version
aws-cli/2.34.39 Python/3.14.4 Linux/6.17.0-1012-aws exe/x86_64.ubuntu.24

ubuntu@ip-172-31-43-28:~$ eksctl version
0.225.0

ubuntu@ip-172-31-43-28:~$ aws sts get-caller-identity
{
    "UserId": "AIDAVI2OVS5PMPVQCSICF",
    "Account": "362552858462",
    "Arn": "arn:aws:iam::362552858462:user/aws_admin"
}

```


## Phase 2
### Step 1: Create the Cluster Configuration File
Instead of a giant command, create a file named `cluster.yaml` on your EC2:

```
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: devops-project-eks
  region: us-east-1
  version: "1.30" # Using a stable, modern K8s version

managedNodeGroups:
  - name: standard-nodes
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 1
    maxSize: 3
    volumeSize: 20
    ssh:
      allow: true # This allows you to SSH into nodes if needed for debugging
```


### Step 2: Launch the Cluster
Now, run the command to start the creation process.

**Warning:** This will take about **15 to 20 minutes**. AWS is busy in the background creating a new VPC, Subnets, Internet Gateways, the EKS Control Plane, and your Worker Nodes.

```
eksctl create cluster -f cluster.yaml
```
app.py:

```python
from flask import Flask, render_template_string, request, redirect
import pymysql
import os
import boto3

app = Flask(__name__)

# Fetch environment variables from K8s
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')

DB_NAME = os.environ.get('DB_NAME', 'devops_db')
REGION = "us-east-1"

def get_conn():
    rds_client = boto3.client('rds', region_name=REGION)
    # gitleaks:allow
    token = rds_client.generate_db_auth_token(
        DBHostname=DB_HOST, 
        Port=3306, 
        DBUsername=DB_USER,
        Region=REGION
    )
    
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=token,
        database=DB_NAME,
        port=3306,
        ssl={'ca': 'global-bundle.pem'},
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    ) 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Visitor Book</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; display: flex; flex-direction: column; align-items: center; }
        .header { background-color: #1a73e8; color: white; width: 100%; text-align: center; padding: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); width: 90%; max-width: 600px; margin-top: 2rem; }
        .tech-stack { background: #e8f0fe; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; text-align: left; }
        .tech-stack ul { list-style-type: none; padding: 0; margin: 0; }
        .tech-stack li { color: #1967d2; font-weight: bold; margin-bottom: 5px; }
        input, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #34a853; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 1rem; }
        button:hover { background-color: #2d8e47; }
        .visitor-card { border-left: 5px solid #1a73e8; background: #fafafa; padding: 10px; margin-top: 10px; border-radius: 4px; text-align: left; }
        .status { font-weight: bold; color: {{ "green" if "✅" in db_status else "red" }}; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cloud-Native Visitor Book</h1>
    </div>
    <div class="container">
        <div class="tech-stack">
            <h3>🚀 Tech Stack Deployed:</h3>
            <ul>
                <li>🐳 Docker: Ingress-> Load Balancer, Probes, Resource: Request and Limit, Multi-Stage Dockerfile</li>
                <li>☸️ Prometheus  </li>
                <li>📊 Grafana  </li>
                <li>🤫 DevSecOps Tools: GitLeaks, SonarQube, Trivy(Install First)</li>
                <li>🤖 Jenkins: Shared Lib, Cred, Env Var, (IAM IRSA Integration)</li>
                <li>☁️ AWS: EC2, VPC, RDS (IAM Auth Enabled), EKS (Load Balancer)</li>
                
            </ul>
        </div>
        <p>Database Status: <span class="status">{{ db_status }}</span></p>
        <form method="POST">
            <input type="text" name="name" placeholder="Your Name" required>
            <textarea name="message" placeholder="Your Message" rows="3"></textarea>
            <button type="submit">Submit to RDS</button>
        </form>
        <hr>
        <h3>Recent Visitors:</h3>
        {% for entry in visitors %}
        <div class="visitor-card">
            <strong>{{ entry.name }}</strong>: {{ entry.message }} <br>
            <small style="color: #888;">{{ entry.visit_time }}</small>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/health')
def health():
    return "OK", 200

@app.route('/debug')
def debug():
    try:
        # This checks which IAM role the Pod is actually using
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return {
            "Status": "IAM Identity Found",
            "Arn": identity.get('Arn'),
            "Account": identity.get('Account')
        }
    except Exception as e:
        return {"Error": str(e)}, 500


@app.route('/', methods=['GET', 'POST'])
def index():
    db_status = "Disconnected ❌"
    visitors = []

    try:
        conn = get_conn()
        db_status = "Connected ✅"
        
        if request.method == 'POST':
            name = request.form.get('name')
            message = request.form.get('message')
            if name and message:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO visitors (name, message) VALUES (%s, %s)"
                    cursor.execute(sql, (name, message))
                conn.commit()
                conn.close() # Close before redirect
                return redirect('/')

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM visitors ORDER BY visit_time DESC")
            visitors = cursor.fetchall()
        conn.close()

    except Exception as e:
        db_status = f"Error: {str(e)} ❌"

    return render_template_string(HTML_TEMPLATE, db_status=db_status, visitors=visitors)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
```


app-deploy.yaml:

```
apiVersion: v1
kind: Namespace

metadata:
  name: my-ns
---
apiVersion: v1
kind: Service
metadata:
  name: my-svc
  namespace: my-ns
spec:
  type: LoadBalancer # add LoadBalancer
  selector:
    app: my-web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
---
kind: Secret
apiVersion: v1

metadata:
  name: mysql-sec
  namespace: my-ns

type: opaque
data:
stringData:  # Use stringData to put plain text; K8s will encode it for you
  host: "database-v1.cih84c6osdd0.us-east-1.rds.amazonaws.com"
  user: "iam_user" # for IAM Auth when use Load Balancer

  dbname: "devops_db" # Update this from 'mysql' to your new database name # Based on your 'show databases' output
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-dep
  namespace: my-ns
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-web
  template:
    metadata:
      labels:
        app: my-web
    spec:
      serviceAccountName: rds-auth-sa
      containers:
      - name: my-pod
        image: yashmane108/simple-app:REPLACE_ME
        securityContext:
          privileged: false
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1001
        imagePullPolicy: Always
        ports:
        - containerPort: 80
        # AWS RDS 
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: host
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: user

        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: mysql-sec
              key: dbname
        resources:
          requests:
            memory: "64Mi"   # Guaranteed 64 Megabytes
            cpu: "100m"      # 10% of 1 CPU core
          limits:
            memory: "128Mi"  # Hard cap at 128 Megabytes
            cpu: "500m"       # Max 50% of 1 CPU core
        # --- ADD PROBES BELOW ---
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 45
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3      # Check every 15 seconds
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30  # Start checking almost immediately
          periodSeconds: 15        # Check often for traffic routing
          timeoutSeconds: 5
          failureThreshold: 3
---
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2

metadata:
  name: my-hpa
  namespace: my-ns

spec:
  scaleTargetRef:
    name: my-dep
    kind: Deployment
    apiVersion: apps/v1

  minReplicas: 1
  maxReplicas: 2

  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ing
  namespace: my-ns
#  annotations:
#    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-svc
            port:
              number: 80
```


### Step 3: What to watch for while you wait
You don't have to just sit there! You can monitor the progress in two ways:

1. **Terminal:** `eksctl`  will give you live updates (e.g., "building VPC," "creating CloudFormation stack").
2. **AWS Console:** Go to **CloudFormation**. You will see a stack named `eksctl-devops-project-eks-cluster`  being built. This is the "engine" `eksctl`  uses to talk to AWS.
```
ubuntu@ip-172-31-43-28:~/simple-web/eks$ eksctl create cluster -f cluster.yaml
2026-04-30 14:48:54 [ℹ]  eksctl version 0.225.0
2026-04-30 14:48:54 [ℹ]  using region us-east-1
2026-04-30 14:48:54 [ℹ]  setting availability zones to [us-east-1f us-east-1a]
2026-04-30 14:48:54 [ℹ]  subnets for us-east-1f - public:192.168.0.0/19 private:192.168.64.0/19
2026-04-30 14:48:54 [ℹ]  subnets for us-east-1a - public:192.168.32.0/19 private:192.168.96.0/19
2026-04-30 14:48:54 [ℹ]  nodegroup "standard-nodes" will use "" [AmazonLinux2023/1.30]
2026-04-30 14:48:54 [ℹ]  using SSH public key "/home/ubuntu/.ssh/id_rsa.pub" as "eksctl-devops-project-eks-nodegroup-standard-nodes-5c:f6:76:d3:32:a7:b7:a0:63:d6:15:76:5a:ec:f9:26"
2026-04-30 14:48:54 [!]  Auto Mode will be enabled by default in an upcoming release of eksctl. This means managed node groups and managed networking add-ons will no longer be created by default. To maintain current behavior, explicitly set 'autoModeConfig.enabled: false' in your cluster configuration. Learn more: https://eksctl.io/usage/auto-mode/
2026-04-30 14:48:54 [ℹ]  using Kubernetes version 1.30
2026-04-30 14:48:54 [ℹ]  creating EKS cluster "devops-project-eks" in "us-east-1" region with managed nodes
2026-04-30 14:48:54 [ℹ]  1 nodegroup (standard-nodes) was included (based on the include/exclude rules)
2026-04-30 14:48:54 [ℹ]  will create a CloudFormation stack for cluster itself and 1 managed nodegroup stack(s)
2026-04-30 14:48:54 [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=us-east-1 --cluster=devops-project-eks'
2026-04-30 14:48:54 [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=false} for cluster "devops-project-eks" in "us-east-1"
2026-04-30 14:48:54 [ℹ]  CloudWatch logging will not be enabled for cluster "devops-project-eks" in "us-east-1"
2026-04-30 14:48:54 [ℹ]  you can enable it with 'eksctl utils update-cluster-logging --enable-types={SPECIFY-YOUR-LOG-TYPES-HERE (e.g. all)} --region=us-east-1 --cluster=devops-project-eks'
2026-04-30 14:48:54 [ℹ]  default addons coredns, metrics-server, vpc-cni, kube-proxy were not specified, will install them as EKS addons
2026-04-30 14:48:54 [ℹ]
2 sequential tasks: { create cluster control plane "devops-project-eks",
    2 sequential sub-tasks: {
        2 sequential sub-tasks: {
            1 task: { create addons },
            wait for control plane to become ready,
        },
        create managed nodegroup "standard-nodes",
    }
}
2026-04-30 14:48:54 [ℹ]  building cluster stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:48:54 [ℹ]  deploying stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:49:24 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:49:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:50:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:51:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:52:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:53:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:54:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:55:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:56:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:57:55 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-cluster"
2026-04-30 14:57:56 [ℹ]  creating addon: coredns
2026-04-30 14:57:56 [ℹ]  successfully created addon: coredns
2026-04-30 14:57:56 [!]  recommended policies were found for "vpc-cni" addon, but since OIDC is disabled on the cluster, eksctl cannot configure the requested permissions; the recommended way to provide IAM permissions for "vpc-cni" addon is via pod identity associations; after addon creation is completed, add all recommended policies to the config file, under `addon.PodIdentityAssociations`, and run `eksctl update addon`
2026-04-30 14:57:56 [ℹ]  creating addon: vpc-cni
2026-04-30 14:57:57 [ℹ]  successfully created addon: vpc-cni
2026-04-30 14:57:57 [ℹ]  creating addon: kube-proxy
2026-04-30 14:57:57 [ℹ]  successfully created addon: kube-proxy
2026-04-30 14:59:58 [ℹ]  building managed nodegroup stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 14:59:58 [ℹ]  deploying stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 14:59:58 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 15:00:28 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 15:01:01 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 15:01:33 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 15:02:08 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-nodegroup-standard-nodes"
2026-04-30 15:02:08 [ℹ]  waiting for the control plane to become ready
2026-04-30 15:02:09 [✔]  saved kubeconfig as "/home/ubuntu/.kube/config"
2026-04-30 15:02:09 [ℹ]  no tasks
2026-04-30 15:02:09 [✔]  all EKS cluster resources for "devops-project-eks" have been created
2026-04-30 15:02:09 [ℹ]  nodegroup "standard-nodes" has 2 node(s)
2026-04-30 15:02:09 [ℹ]  node "ip-192-168-18-47.ec2.internal" is ready
2026-04-30 15:02:09 [ℹ]  node "ip-192-168-48-126.ec2.internal" is ready
2026-04-30 15:02:09 [ℹ]  waiting for at least 1 node(s) to become ready in "standard-nodes"
2026-04-30 15:02:09 [ℹ]  nodegroup "standard-nodes" has 2 node(s)
2026-04-30 15:02:09 [ℹ]  node "ip-192-168-18-47.ec2.internal" is ready
2026-04-30 15:02:09 [ℹ]  node "ip-192-168-48-126.ec2.internal" is ready
2026-04-30 15:02:09 [✔]  created 1 managed nodegroup(s) in cluster "devops-project-eks"
2026-04-30 15:02:10 [ℹ]  creating addon: metrics-server
2026-04-30 15:02:10 [ℹ]  successfully created addon: metrics-server
2026-04-30 15:02:11 [ℹ]  kubectl command should work with "/home/ubuntu/.kube/config", try 'kubectl get nodes'
2026-04-30 15:02:11 [✔]  EKS cluster "devops-project-eks" in "us-east-1" region is ready
ubuntu@ip-172-31-43-28:~/simple-web/eks$
```
If you look closely at your logs, there was a small warning:

> `[!] recommended policies were found for "vpc-cni" addon, but since OIDC is disabled on the cluster, eksctl cannot configure the requested permissions` 

This is exactly what we need for **IRSA** (IAM Roles for Service Accounts). We need to enable the **OIDC Provider** so EKS can talk to AWS IAM.

**Run this command to enable it (it only takes 1 minute):**

```
eksctl utils associate-iam-oidc-provider --region=us-east-1 --cluster=devops-project-eks --approve
```
#### Verify the Cluster
```
# Verify the nodes are online and running K8s v1.30
kubectl get nodes

# See the 'System' pods (like coredns and kube-proxy) running
kubectl get pods -A
```


### Phase 3 
IAM Policy

Service Account



The IRSA Setup (No More Passwords)

Now we will create the bridge between Kubernetes and AWS IAM. Run these commands on your EC2:

**Step A: Create an IAM Policy** Create a file named `rds-policy.json`  in project folder(github)

JSON

```
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Effect": "Allow",
         "Action": ["rds-db:connect"],
         "Resource": ["arn:aws:rds-db:us-east-1:362552858462:dbuser:*/iam_user"]
      }
   ]
}
```
at * use db resource id and at admin used other name which user has AWSAuthenticationPlugin

like this 



mysql> SELECT user, host, plugin FROM mysql.user WHERE user = 'iam_user';

+----------+------+-------------------------+

| user | host | plugin |

+----------+------+-------------------------+

| iam_user | % | AWSAuthenticationPlugin |

+----------+------+-------------------------+



Run this on ec2(any user where aws login done) to create the policy: must check last path of this cmd 

```
aws iam create-policy --policy-name EKS-RDS-Auth-Policy --policy-document file://k8s/rds-policy.json
```
**Step B: Create the Service Account** This command links a Kubernetes Service Account to an IAM Role automatically.

```
eksctl create iamserviceaccount \
--name rds-auth-sa \
--namespace my-ns \
--cluster devops-project-eks \
--role-name eks-rds-auth-role \
--attach-policy-arn arn:aws:iam::362552858462:policy/EKS-RDS-Auth-Policy \
--approve
```
output 

```
ubuntu@ip-172-31-43-28:~/simple-web/eks$ eksctl create iamserviceaccount \
    --name rds-auth-sa \
    --namespace my-ns \
    --cluster devops-project-eks \
    --role-name eks-rds-auth-role \
    --attach-policy-arn arn:aws:iam::362552858462:policy/EKS-RDS-Auth-Policy \
    --approve \
    --override-existing-serviceaccounts
2026-05-01 06:54:04 [ℹ]  1 iamserviceaccount (my-ns/rds-auth-sa) was included (based on the include/exclude rules)
2026-05-01 06:54:04 [!]  metadata of serviceaccounts that exist in Kubernetes will be updated, as --override-existing-serviceaccounts was set
2026-05-01 06:54:04 [ℹ]  1 task: {
    2 sequential sub-tasks: {
        create IAM role for serviceaccount "my-ns/rds-auth-sa",
        create serviceaccount "my-ns/rds-auth-sa",
    } }2026-05-01 06:54:04 [ℹ]  building iamserviceaccount stack "eksctl-devops-project-eks-addon-iamserviceaccount-my-ns-rds-auth-sa"
2026-05-01 06:54:04 [ℹ]  deploying stack "eksctl-devops-project-eks-addon-iamserviceaccount-my-ns-rds-auth-sa"
2026-05-01 06:54:04 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-addon-iamserviceaccount-my-ns-rds-auth-sa"
2026-05-01 06:54:34 [ℹ]  waiting for CloudFormation stack "eksctl-devops-project-eks-addon-iamserviceaccount-my-ns-rds-auth-sa"
2026-05-01 06:54:34 [ℹ]  created serviceaccount "my-ns/rds-auth-sa"
ubuntu@ip-172-31-43-28:~/simple-web/eks$
```
Even after creating the IAM Role, **RDS will still reject the connection** unless you enable IAM Authentication on the database itself.

**Run this command to enable IAM Auth on your RDS instance:**

```
aws rds modify-db-instance \
--db-instance-identifier database-1 \
--apply-immediately \
--enable-iam-database-authentication
```


# Grafana and Prometheus
## Phase 1: Install the Prometheus Stack
We will use the **kube-prometheus-stack**. It is an "all-in-one" solution that includes Prometheus, Grafana, and Alertmanager.

### 1. Install Helm on your Ubuntu instance
If you don't have Helm yet, run these commands:

Bash

```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```
### 2. Add the Prometheus Repository
Bash

```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```
### 3. Deploy the Stack
We will create a new namespace called `monitoring` to keep things organized.

Bash

```
kubectl create namespace monitoring
helm install prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring
```
---

## Phase 2: Accessing the Dashboards
By default, these services are not exposed to the internet for security. We will use **Port Forwarding** to see them on your browser.

### 1. Access Grafana
Find the name of your Grafana pod:

```
kubectl get pods -n monitoring | grep grafana
```
Forward the port (replace `<pod-name>` with your actual pod name):

```
kubectl port-forward <pod-name-from-above-output> 3000:3000 -n monitoring --address 0.0.0.0
```
- **URL**: `http://<your-ubuntu-ip>:3000` 
- **User**: `admin` 
- **Password**: `prom-operator`  (This is the default; we can change it later). 

if Login failed
Invalid username or password then run this 
```
kubectl get secret prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```


```
ubuntu@ip-172-31-43-28:~$ kubectl get all -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-prometheus-stack-kube-prom-alertmanager-0   2/2     Running   0          27m
pod/prometheus-prometheus-stack-kube-prom-prometheus-0       2/2     Running   0          27m
pod/prometheus-stack-grafana-79f5b48f99-4wpdb                3/3     Running   0          27m
pod/prometheus-stack-kube-prom-operator-6dc8dc846c-6mhh2     1/1     Running   0          27m
pod/prometheus-stack-kube-state-metrics-566586f568-rv6jf     1/1     Running   0          27m
pod/prometheus-stack-prometheus-node-exporter-xzfdm          1/1     Running   0          27m
pod/prometheus-stack-prometheus-node-exporter-zqzls          1/1     Running   0          27m

NAME                                                TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                       ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   27m
service/prometheus-operated                         ClusterIP   None             <none>        9090/TCP                     27m
service/prometheus-stack-grafana                    ClusterIP   10.100.140.137   <none>        80/TCP                       27m
service/prometheus-stack-kube-prom-alertmanager     ClusterIP   10.100.246.57    <none>        9093/TCP,8080/TCP            27m
service/prometheus-stack-kube-prom-operator         ClusterIP   10.100.109.98    <none>        443/TCP                      27m
service/prometheus-stack-kube-prom-prometheus       ClusterIP   10.100.64.112    <none>        9090/TCP,8080/TCP            27m
service/prometheus-stack-kube-state-metrics         ClusterIP   10.100.244.194   <none>        8080/TCP                     27m
service/prometheus-stack-prometheus-node-exporter   ClusterIP   10.100.241.36    <none>        9100/TCP                     27m

NAME                                                       DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
daemonset.apps/prometheus-stack-prometheus-node-exporter   2         2         2       2            2           kubernetes.io/os=linux   27m

NAME                                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/prometheus-stack-grafana              1/1     1            1           27m
deployment.apps/prometheus-stack-kube-prom-operator   1/1     1            1           27m
deployment.apps/prometheus-stack-kube-state-metrics   1/1     1            1           27m

NAME                                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/prometheus-stack-grafana-79f5b48f99              1         1         1       27m
replicaset.apps/prometheus-stack-kube-prom-operator-6dc8dc846c   1         1         1       27m
replicaset.apps/prometheus-stack-kube-state-metrics-566586f568   1         1         1       27m

NAME                                                                    READY   AGE
statefulset.apps/alertmanager-prometheus-stack-kube-prom-alertmanager   1/1     27m
statefulset.apps/prometheus-prometheus-stack-kube-prom-prometheus       1/1     27m

ubuntu@ip-172-31-43-28:~$ kubectl get secrets -n monitoring
NAME                                                                                  TYPE                 DATA   AGE
alertmanager-prometheus-stack-kube-prom-alertmanager                                  Opaque               1      29m
alertmanager-prometheus-stack-kube-prom-alertmanager-cluster-tls-config               Opaque               1      29m
alertmanager-prometheus-stack-kube-prom-alertmanager-generated                        Opaque               1      29m
alertmanager-prometheus-stack-kube-prom-alertmanager-tls-assets-0                     Opaque               0      29m
alertmanager-prometheus-stack-kube-prom-alertmanager-web-config                       Opaque               1      29m
prometheus-prometheus-stack-kube-prom-prometheus                                      Opaque               1      29m
prometheus-prometheus-stack-kube-prom-prometheus-thanos-prometheus-http-client-file   Opaque               1      29m
prometheus-prometheus-stack-kube-prom-prometheus-tls-assets-0                         Opaque               1      29m
prometheus-prometheus-stack-kube-prom-prometheus-web-config                           Opaque               1      29m
prometheus-stack-grafana                                                              Opaque               3      29m
prometheus-stack-kube-prom-admission                                                  Opaque               3      29m
sh.helm.release.v1.prometheus-stack.v1                                                helm.sh/release.v1   1      29m

```
![image.png](https://eraser.imgix.net/workspaces/4RtejTS1x6R6vPrVgMOW/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_Jg3NsPPkGsBL5YyGaN58A.png?ixlib=js-3.8.0 "image.png")


Create console point 

name: Email

add email add

under notification policies select email-alert Default contact point

and when pods at ImagePullBackOff then we see this (see below img)



create alert rule 

name ImagePullBackOff Alert

query: sum(kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}) > 0

select email-alert contact point



![image.png](https://eraser.imgix.net/workspaces/4RtejTS1x6R6vPrVgMOW/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_4FATpnkZDlRAlimlJiZ9O.png?ixlib=js-3.8.0 "image.png")





create new job on jenkins pipeline

tick Trigger builds remotely (e.g., from scripts)

Authentication token: `fix123` 

```
http://﻿﻿3.82.111.130:8080/job/visitor-book-auto-fix/build?token=fix123 
```
Pipeline script 

```
pipeline {
    agent any

    stages {
        stage('Check Pods') {
            steps {
                sh 'kubectl get pods -n my-ns'
            }
        }

        stage('Restart Deployment') {
            steps {
                sh 'kubectl rollout restart deployment my-dep -n my-ns'
            }
        }

        stage('Verify') {
            steps {
                sh 'kubectl get pods -n my-ns'
            }
        }
    }
}
```
and when pods at ImagePullBackOff

see started by remote host mean done

![image.png](https://eraser.imgix.net/workspaces/4RtejTS1x6R6vPrVgMOW/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_AFg9TVf-_H8Rn7wpn7xXK.png?ixlib=js-3.8.0 "image.png")





# MOVE TO DEVSECOPS


- [x] GitLeaks Scan — Detects sensitive data (API keys, tokens, passwords) in source code.
- [x] sonarQube: Checks code quality (bugs, duplication, code smells).
- [x] Trivy: Detects vulnerabilities in dependencies. 
- [x] Cosign: Sign Docker images. 
- [x] Kyverno: No root containers, No latest tag, Must have resource limits. 



## GitLeaks Scan:
```
stage('Secret Scanning (Gitleaks)') {
    steps {
        script {
            echo "🛡️ Starting Security Gate 1: Gitleaks"
            sh '''
            docker run --rm -v $(pwd):/path ghcr.io/gitleaks/gitleaks:latest detect \
            --source=/path \
            --baseline-path=/path/.gitleaks-baseline.json
            '''
        }
    }
}
```
## SonarQube:
default username and pass is `admin` 

```
docker run -d --name sonarqube \
-p 9000:9000 \
sonarqube:lts-community
```
open 9000 port in EC2 SG

generate User Token and add in jenkins credentials 

```
stage('SonarQube Scan') {
    steps {
        withCredentials([string(credentialsId: 'sonarQ-token', variable: 'SONAR_TOKEN')]) {
            sh """
            docker run --rm \
            -e SONAR_HOST_URL="http://3.82.111.130:9000" \
            -e SONAR_SCANNER_OPTS="-Dsonar.projectKey=visitor-book" \
            -e SONAR_TOKEN="${SONAR_TOKEN}" \
            -v "\$(pwd):/usr/src" \
            sonarsource/sonar-scanner-cli 
            """
        }
    }
}
```
## Trivy:
```
stage('Trivy: File Scan') {
    steps {
        sh '''
        trivy fs \
        --exit-code 1 \
        --severity HIGH,CRITICAL \
        .
        '''
    }
}

stage('Docker: Build Image') {
    steps {
        sh "docker build -t simple-app:${env.Tag} ."
    }
}

stage('Trivy: DImage Scan') {
    steps {
        sh "trivy image --exit-code 1 --severity CRITICAL simple-app:${env.Tag}"
    }
}

stage("Trivy: K8s Yaml Scan") {
    steps {
        sh "trivy config ./k8s/ "
    }
}
```
## Cosign
create password, private and public key first then add that in pipeline cred

```
stage('Cosign Sign'){
    steps{
        withCredentials([
            file(credentialsId: 'fCredID', variable: 'COSIGN_KEY'),
            string(credentialsId: 'sCredID', variable: 'COSIGN_PASSWORD')
        ]) {
            sh """
            export COSIGN_PASSWORD="$COSIGN_PASSWORD"
                            
            cosign sign --key "$COSIGN_KEY" yashmane108/simple-app:${env.Tag}
            """
           }
     }
}
```
## kyverno
no need to add in pipeline 

kyverno-policy.yaml

```
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-latest-tag
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: require-image-tag
      match:
        any:
        - resources:
            kinds:
            - Pod
      validate:
        message: "Using 'latest' tag is not allowed."
        pattern:
          spec:
            containers:
            - image: "!*:latest"
    - name: privileged-containers
      match:
        any:
        - resources:
            kinds:
            - Pod
      validate:
        message: "Privileged containers are not allowed."
        pattern:
          spec:
            containers:
            - securityContext:
                privileged: false
    - name: check-resource
      match:
        any:
        - resources:
            kinds:
            - Pod
      validate:
        message: "CPU and memory requests/limits are required."
        pattern:
          spec:
            containers:
            - resources:
                requests:
                  memory: "?*"
                  cpu: "?*"
                limits:
                  memory: "?*"
                  cpu: "?*"

    - name: check-run-as-nonroot
      match:
        any:
        - resources:
            kinds:
            - Pod
      validate:
        message: "Containers must run as non-root users."
        pattern:
          spec:
            containers:
            - securityContext:
                runAsNonRoot: true
```
# Helm


To Use Helm 

```
helm install helm-app ./my-chart -n helm-ns
```

Jenkins PIPELINE:

```
@Library('Shared') _

pipeline {
    agent any

    environment {
        TAG = "v${env.BUILD_NUMBER}"
        KUBECONFIG = '/home/ubuntu/.kube/config'
    }

    stages {

        stage('GitHub: Git Clone') {
            steps {
                gitClone("https://github.com/yashmane108/DevOps-P1.git", "master")
            }
        }

        stage('Gitleaks: Secrets Scan') {
            steps {
                script {
                    echo "Running Gitleaks Secret Scan..."

                    sh '''
                    docker run --rm \
                    -v $(pwd):/path \
                    ghcr.io/gitleaks/gitleaks:latest detect \
                    --source=/path \
                    --baseline-path=/path/.gitleaks-baseline.json
                    '''

                    echo "No hardcoded secrets detected"
                }
            }
        }

        stage('SonarQube: Code Scan') {
            steps {
                sonarToken("sonarQ-token")
            }
        }

        stage('Trivy: File System Scan') {
            steps {
                sh '''
                trivy fs \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                .
                '''
            }
        }

        stage('Docker: Build Image') {
            steps {
                sh "docker build -t yashmane108/simple-app:${TAG} ."
            }
        }

        stage('Trivy: Image Scan') {
            steps {
                sh '''
                trivy image \
                --exit-code 1 \
                --severity HIGH,CRITICAL \
                yashmane108/simple-app:${TAG}
                '''
            }
        }

        stage('Trivy: Kubernetes YAML Scan') {
            steps {
                sh "trivy config ./k8s/"
            }
        }

        stage('Docker: Push Image') {
            steps {
                dockerHubPushCred("dockerCred", "simple-app")
            }
        }

        stage('Cosign: Image Signing') {
            steps {
                cosign("cosign-private-key", "cosign-password")
            }
        }

        stage('Terraform: Drift Detection & Recovery') {
            steps {
                dir('terraform') {
                    script {

                        def exitCode = sh(
                            script: 'terraform plan -detailed-exitcode',
                            returnStatus: true
                        )

                        if (exitCode == 2) {

                            echo "⚠️ Infrastructure drift detected!"

                            sh 'terraform apply --auto-approve'

                            echo "✅ Infrastructure restored successfully"

                        } else if (exitCode == 0) {

                            echo "✅ No infrastructure drift detected"

                        } else {

                            error "Terraform plan failed"

                        }
                    }
                }
            }
        }

        stage('Kubernetes: Apply Kyverno Policies') {
            steps {
                sh "kubectl apply -f k8s/kyverno-policy.yaml"
            }
        }

        stage('Helm: Deploy Application') {
            steps {

                sh """
                helm upgrade --install my-app ./my-chart \
                --namespace my-ns \
                --create-namespace \
                --set image.tag=${TAG}
                """
            }
        }

        stage('Kubernetes: Health Check & Self-Healing') {
            steps {
                script {

                    try {

                        echo "Checking deployment rollout status..."

                        sh '''
                        kubectl rollout status deployment/my-dep \
                        -n my-ns \
                        --timeout=180s
                        '''

                        echo "✅ Deployment successful"

                        sh '''
                        kubectl get pods -n my-ns
                        '''

                        def podStatus = sh(
                            script: '''
                            kubectl get pods -n my-ns --no-headers | \
                            grep -E "CrashLoopBackOff|ImagePullBackOff|ErrImagePull" || true
                            ''',
                            returnStdout: true
                        ).trim()

                        if (podStatus) {

                            echo "❌ Pod issue detected:"
                            echo podStatus

                            echo "⚠️ Starting automatic rollback..."

                            sh "helm rollback my-app"

                            error "Self-healing triggered due to unhealthy pods"
                        }

                    } catch (Exception e) {

                        echo "❌ Deployment unhealthy"

                        echo "⚠️ Rolling back to previous stable version..."

                        sh "helm rollback my-app"

                        error "Deployment failed and rollback completed"
                    }
                }
            }
        }
    }
}
```
To clean EKS 

```
eksctl delete cluster --name devops-project-eks --region us-east-1
```


