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
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306,
 #       ssl={'ca': 'global-bundle.pem'},
        charset='utf8mb4',
  #      cursorclass=pymysql.cursors.DictCursor,
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
