# Saleor SRE Project: Production-Heavy E-Commerce Platform

This project deploys [Saleor](https://github.com/saleor/saleor) as a production-grade e-commerce platform on AWS, tailored for the Morrisons Site Reliability Engineer (SRE) role. It demonstrates CI/CD, AWS services, monitoring, automation, and secure practices, addressing job description (JD) skills: GitHub, Jenkins, Terraform, Ansible, Docker, AWS (EC2, EKS, ECS, Fargate, Lambda, S3), testing (pytest/Selenium), SpringBoot, observability, and soft skills (communication, influencing).

**Why Production-Heavy?**
- Past role: Struggled with complex production infra; this builds confidence for enterprise scale.
- JD: Requires "advancing SRE practices at enterprise scale," "high availability, performance."
- Continuous Learning: Maintain repo to refine skills (e.g., Jenkins, SpringBoot).

**Environments**
- **Dev**: Local machine (code, test locally, `dev` branch).
- **Staging**: AWS EC2 (staging.fazio.live, test/validate, `staging` branch).
- **Production**: AWS EKS (fazio.live, live site, `main` branch).

**Timeline**: 7 days (complete by interview).

## Checklist

### Day 1: GitHub Repo and Domain Setup
- [ ] **Fork Saleor Repo**
  - Fork [github.com/saleor/saleor](https://github.com/saleor/saleor) to `github.com/your-username/saleor`.
  - Clone locally: `git clone https://github.com/your-username/saleor.git`.
- [ ] **Set Up Branches**
  - Create: `dev`, `staging`, `main`.
  - Commands:
    ```bash
    cd saleor
    git checkout -b dev
    git push origin dev
    git checkout -b staging
    git push origin staging
    git checkout main
    git push origin main
    ```
  - Protect `staging`, `main` (GitHub → Settings → Branches):
    - Require PRs, passing tests.
- [ ] **Buy Domain (fazio.live)**
  - Use **Namecheap** (~$12/year):
    - Search "fazio.live" → Buy → Checkout.
    - If unavailable, try fazio-shop.live.
  - Alternative: **AWS Route 53** (AWS Console → Route 53 → Register Domain).
- [ ] **Configure Cloudflare DNS**
  - Create **Cloudflare** account (free plan).
  - Add site: fazio.live → Free Plan.
  - Update nameservers at registrar (e.g., Namecheap → Manage → Custom DNS → Add Cloudflare’s ns1.cloudflare.com, ns2.cloudflare.com).
  - Wait ~24h for propagation.
- [ ] **Test Locally**
  - Run Saleor: `docker-compose up`.
  - Access: http://localhost:8000.
- **JD Skills**: GitHub, Docker, secure practices (Cloudflare prep), SDLC.

### Day 2: Staging on EC2
- [ ] **Provision EC2**
  - Save as `ec2.tf`:
    ```hcl
    provider "aws" {
      region = "eu-west-1"
    }
    resource "aws_instance" "saleor_staging" {
      ami           = "ami-0c55b159cbfafe1f0" # Amazon Linux 2
      instance_type = "t3.medium"
      key_name      = "saleor-key"
      vpc_security_group_ids = [aws_security_group.saleor_sg.id]
      tags = {
        Name        = "saleor-staging"
        Environment = "staging"
      }
    }
    resource "aws_security_group" "saleor_sg" {
      name        = "saleor-staging-sg"
      ingress {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
      ingress {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
      ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
      egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
      }
    }
    ```
  - Run: `terraform init`, `terraform apply`.
  - Note EC2 IP (e.g., 54.XX.XX.XX).
- [ ] **Configure EC2 with Ansible**
  - Install Ansible: `pip install ansible`.
  - Save as `inventory.yml`:
    ```yaml
    all:
      hosts:
        staging:
          ansible_host: <EC2-IP>
          ansible_user: ec2-user
          ansible_ssh_private_key_file: ~/.ssh/saleor-key.pem
    ```
  - Save as `setup-ec2.yml`:
    ```yaml
    - name: Configure EC2 for Saleor
      hosts: staging
      become: yes
      tasks:
        - name: Install Docker
          yum:
            name: docker
            state: latest
        - name: Start Docker
          service:
            name: docker
            state: started
            enabled: yes
        - name: Install Docker Compose
          get_url:
            url: "https://github.com/docker/compose/releases/latest/download/docker-compose-Linux-x86_64"
            dest: /usr/local/bin/docker-compose
            mode: '0755'
        - name: Install Nginx
          yum:
            name: nginx
            state: latest
        - name: Configure Nginx
          copy:
            content: |
              server {
                listen 80;
                server_name staging.fazio.live;
                location /stub_status {
                  stub_status;
                }
                location / {
                  proxy_pass http://localhost:8000;
                  proxy_set_header Host $host;
                  proxy_set_header X-Real-IP $remote_addr;
                }
              }
            dest: /etc/nginx/conf.d/saleor.conf
        - name: Restart Nginx
          service:
            name: nginx
            state: restarted
    ```
  - Run: `ansible-playbook -i inventory.yml setup-ec2.yml`.
- [ ] **Deploy Saleor**
  - SSH: `ssh -i saleor-key.pem ec2-user@<EC2-IP>`.
  - Clone repo: `git clone https://github.com/your-username/saleor.git`.
  - Run: `cd saleor && docker-compose up -d`.
- [ ] **Cloudflare SSL**
  - Add A record: Name: staging, Value: <EC2-IP>, Proxy: Enabled.
  - SSL/TLS → Full (strict), Always Use HTTPS.
  - Test: https://staging.fazio.live.
- [ ] **Secrets**
  - Store `DATABASE_URL` in SSM:
    ```bash
    aws ssm put-parameter --name /saleor/DATABASE_URL --value "postgres://user:pass@rds:5432/saleor" --type SecureString
    ```
  - Update `docker-compose.yml`:
    ```yaml
    environment:
      - DATABASE_URL=$(aws ssm get-parameter --name /saleor/DATABASE_URL --with-decryption --query Parameter.Value --output text)
    ```
- [ ] **Monitor EC2**
  - Install CloudWatch Agent:
    ```bash
    sudo yum install amazon-cloudwatch-agent -y
    sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
    ```
  - Start: `sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a start`.
  - AWS Console → CloudWatch → Alarms → Create:
    - Metric: CPUUtilization, Threshold: >80%, Action: Email.
- **JD Skills**: EC2, Docker, Terraform, Ansible, testing (prep), monitoring (CloudWatch), secure practices (SSM, Cloudflare).

### Day 3: Production on EKS
- [ ] **Provision EKS**
  - Save as `eks.tf`:
    ```hcl
    provider "aws" {
      region = "eu-west-1"
    }
    module "eks" {
      source  = "terraform-aws-modules/eks/aws"
      version = "~> 19.0"
      cluster_name    = "saleor-cluster"
      cluster_version = "1.29"
      subnet_ids      = ["subnet-abc123", "subnet-def456"] # Replace with VPC subnets
      vpc_id          = "vpc-123456"
      eks_managed_node_groups = {
        default = {
          min_size     = 1
          max_size     = 3
          desired_size = 2
          instance_types = ["t3.medium"]
        }
      }
    }
    ```
  - Run: `terraform apply`.
- [ ] **Deploy Saleor**
  - Configure kubectl: `aws eks update-kubeconfig --name saleor-cluster --region eu-west-1`.
  - Save as `saleor.yaml`:
    ```yaml
    apiVersion: v1
    kind: Namespace
    metadata:
      name: saleor
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: saleor
      namespace: saleor
    spec:
      replicas: 2
      selector:
        matchLabels:
          app: saleor
      template:
        metadata:
          labels:
            app: saleor
        spec:
          containers:
          - name: saleor
            image: saleor-ecommerce:latest
            ports:
            - containerPort: 8000
            envFrom:
            - secretRef:
                name: saleor-secrets
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: saleor
      namespace: saleor
    spec:
      ports:
      - port: 80
        targetPort: 8000
      selector:
        app: saleor
      type: LoadBalancer
    ```
  - Apply: `kubectl apply -f saleor.yaml`.
  - Note ELB URL (e.g., abc123.elb.eu-west-1.amazonaws.com).
- [ ] **Cloudflare**
  - Add CNAME: Name: @, Value: <ELB-URL>, Proxy: Enabled.
  - SSL/TLS → Full (strict).
  - Test: https://fazio.live.
- [ ] **Secrets**
  - AWS Secrets Manager → Create Secret:
    - Name: `saleor-secrets`.
    - Keys: `DATABASE_URL`, `SECRET_KEY`.
  - Kubernetes secret:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: saleor-secrets
      namespace: saleor
    type: Opaque
    data:
      DATABASE_URL: <base64-encoded>
      SECRET_KEY: <base64-encoded>
    ```
  - Apply: `kubectl apply -f secret.yaml`.
- [ ] **Monitor EKS**
  - Save as `monitoring.yaml`:
    ```yaml
    apiVersion: v1
    kind: Namespace
    metadata:
      name: monitoring
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: prometheus
      namespace: monitoring
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: prometheus
      template:
        metadata:
          labels:
            app: prometheus
        spec:
          containers:
          - name: prometheus
            image: prom/prometheus:v2.45.0
            args:
            - "--config.file=/etc/prometheus/prometheus.yml"
            ports:
            - containerPort: 9090
            volumeMounts:
            - name: config-volume
              mountPath: /etc/prometheus
          volumes:
          - name: config-volume
            configMap:
              name: prometheus-config
    ---
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: prometheus-config
      namespace: monitoring
    data:
      prometheus.yml: |
        global:
          scrape_interval: 15s
        scrape_configs:
        - job_name: 'saleor'
          static_configs:
          - targets: ['saleor.saleor.svc.cluster.local:8000']
        - job_name: 'postgres'
          static_configs:
          - targets: ['postgres-exporter.monitoring.svc.cluster.local:9187']
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: grafana
      namespace: monitoring
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: grafana
      template:
        metadata:
          labels:
            app: grafana
        spec:
          containers:
          - name: grafana
            image: grafana/grafana:10.0.0
            ports:
            - containerPort: 3000
            env:
            - name: GF_AUTH_ANONYMOUS_ENABLED
              value: "true"
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: grafana
      namespace: monitoring
    spec:
      ports:
      - port: 3000
        targetPort: 3000
      selector:
        app: grafana
      type: LoadBalancer
    ```
  - Apply: `kubectl apply -f monitoring.yaml`.
  - Add CNAME for Grafana (grafana.fazio.live).
- **JD Skills**: EKS, Docker, Kubernetes, Terraform, monitoring (Prometheus/Grafana), secure practices (Secrets Manager, Cloudflare).

### Day 4: CI/CD and Web Server Monitoring
- [ ] **CI/CD with GitHub Actions**
  - Save as `.github/workflows/cicd.yml`:
    ```yaml
    name: Saleor CI/CD
    on:
      push:
        branches:
          - dev
          - staging
          - main
      pull_request:
        branches:
          - staging
          - main
    jobs:
      test:
        runs-on: ubuntu-latest
        services:
          postgres:
            image: postgres:13
            env:
              POSTGRES_DB: saleor
              POSTGRES_USER: saleor
              POSTGRES_PASSWORD: saleor
            ports:
              - 5432:5432
            options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
          redis:
            image: redis:6
            ports:
              - 6379:6379
        steps:
          - uses: actions/checkout@v3
          - uses: actions/setup-python@v4
            with:
              python-version: '3.10'
          - run: |
              pip install flake8 pytest pytest-django selenium
              flake8 . --max-line-length=120 --exclude=venv,migrations
              pytest --ds=saleor.settings
              python tests/e2e_checkout.py
            env:
              SELENIUM_URL: http://staging.fazio.live
      build:
        needs: test
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: docker/login-action@v2
            with:
              username: ${{ secrets.DOCKER_USERNAME }}
              password: ${{ secrets.DOCKER_PASSWORD }}
          - run: |
              docker build -t saleor-ecommerce:${{ github.sha }} .
              docker push saleor-ecommerce:${{ github.sha }}
      deploy-staging:
        needs: build
        if: github.ref == 'refs/heads/staging'
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: aws-actions/configure-aws-credentials@v1
            with:
              aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
              aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
              aws-region: eu-west-1
          - run: |
              aws ec2 describe-instances --filters Name=tag:Environment,Values=staging --query 'Reservations[].Instances[].InstanceId' --output text > instance_ids.txt
              while read -r instance_id; do
                aws ssm send-command \
                  --instance-ids "$instance_id" \
                  --document-name "AWS-RunShellScript" \
                  --parameters '{"commands":["docker pull saleor-ecommerce:'${{ github.sha }}'","docker stop saleor || true","docker rm saleor || true","docker run -d --name saleor -p 8000:8000 --env-file /home/ec2-user/.env saleor-ecommerce:'${{ github.sha }}'"]}' \
                  --comment "Deploy to EC2"
              done < instance_ids.txt
      deploy-prod:
        needs: deploy-staging
        if: github.ref == 'refs/heads/main'
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          - uses: aws-actions/configure-aws-credentials@v1
            with:
              aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
              aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
              aws-region: eu-west-1
          - uses: azure/setup-kubectl@v3
          - run: |
              aws eks update-kubeconfig --name saleor-cluster --region eu-west-1
              kubectl set image deployment/saleor saleor=saleor-ecommerce:${{ github.sha }} -n saleor
              kubectl rollout status deployment/saleor -n saleor
    ```
  - Add secrets (GitHub → Settings → Secrets):
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`.
  - Push to `dev`, PR to `staging`, `main`.
- [ ] **Web Server Monitoring**
  - Add `django-prometheus`:
    ```bash
    echo "django-prometheus" >> requirements.txt
    ```
    ```python
    # saleor/settings.py
    INSTALLED_APPS += ['django_prometheus']
    MIDDLEWARE = ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + MIDDLEWARE + ['django_prometheus.middleware.PrometheusAfterMiddleware']
    ```
  - Nginx exporter (EC2):
    ```bash
    ssh -i saleor-key.pem ec2-user@<EC2-IP>
    docker run -d -p 9113:9113 nginx/nginx-prometheus-exporter:0.11.0 -nginx.scrape-uri=http://localhost:8000/stub_status
    ```
  - EKS exporter:
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: nginx-exporter
      namespace: saleor
    spec:
      selector:
        matchLabels:
          app: nginx-exporter
      template:
        metadata:
          labels:
            app: nginx-exporter
        spec:
          containers:
          - name: nginx-exporter
            image: nginx/nginx-prometheus-exporter:0.11.0
            args:
            - -nginx.scrape-uri=http://saleor:8000/stub_status
            ports:
            - containerPort: 9113
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: nginx-exporter
      namespace: saleor
    spec:
      ports:
      - port: 9113
        targetPort: 9113
      selector:
        app: nginx-exporter
    ```
  - Update Prometheus:
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: prometheus-config
      namespace: monitoring
    data:
      prometheus.yml: |
        global:
          scrape_interval: 15s
        scrape_configs:
        - job_name: 'saleor'
          static_configs:
          - targets: ['saleor.saleor.svc.cluster.local:8000']
        - job_name: 'postgres'
          static_configs:
          - targets: ['postgres-exporter.monitoring.svc.cluster.local:9187']
        - job_name: 'nginx'
          static_configs:
          - targets: ['nginx-exporter.saleor.svc.cluster.local:9113', '<EC2-IP>:9113']
    ```
  - Apply: `kubectl apply -f prometheus-config.yaml`.
  - Grafana dashboards (grafana.fazio.live):
    - Request rate, latency, errors.
    - SLO: 99.9% uptime, <300ms latency.
- [ ] **Secrets**
  - Grafana: `aws secretsmanager create-secret --name grafana-admin --secret-string '{"username":"admin","password":"securepass"}'`.
- **JD Skills**: GitHub, CI/CD, Docker, EC2, EKS, monitoring (Prometheus/Grafana), secure practices.

### Day 5: Database and Additional Monitoring
- [ ] **Database Monitoring**
  - RDS for PostgreSQL (staging/prod):
    - AWS Console → RDS → Create Database (PostgreSQL, free tier).
    - Note endpoint (e.g., saleor.ccs4nlsn.eu-west-1.rds.amazonaws.com).
  - pg_exporter (EKS):
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: postgres-exporter
      namespace: monitoring
    spec:
      selector:
        matchLabels:
          app: postgres-exporter
      template:
        metadata:
          labels:
            app: postgres-exporter
        spec:
          containers:
          - name: postgres-exporter
            image: prometheuscommunity/postgres-exporter:v0.15.0
            env:
            - name: DATA_SOURCE_NAME
              valueFrom:
                secretKeyRef:
                  name: saleor-secrets
                  key: DATABASE_URL
            ports:
            - containerPort: 9187
    ```
  - Apply: `kubectl apply -f pg-exporter.yaml`.
  - CloudWatch: Enable RDS metrics (AWS Console → RDS → Modify → Enhanced Monitoring).
- [ ] **X-Ray**
  - Add SDK:
    ```bash
    pip install aws-xray-sdk
    echo "aws-xray-sdk" >> requirements.txt
    ```
    ```python
    # saleor/settings.py
    MIDDLEWARE += ['aws_xray_sdk.ext.django.XRayMiddleware']
    ```
  - X-Ray daemon (EKS):
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: xray-daemon
      namespace: saleor
    spec:
      selector:
        matchLabels:
          app: xray-daemon
      template:
        metadata:
          labels:
            app: xray-daemon
        spec:
          containers:
          - name: xray-daemon
            image: amazon/aws-xray-daemon:3
            ports:
            - containerPort: 2000
    ```
  - Apply: `kubectl apply -f xray-daemon.yaml`.
- **JD Skills**: Monitoring (CloudWatch, X-Ray), database (PostgreSQL), secure practices.

### Day 6: Testing and Polish
- [ ] **Run Tests**
  - EC2: `ssh -i saleor-key.pem ec2-user@<EC2-IP>`.
  - Install: `pip install pytest pytest-django selenium`.
  - Run: `pytest`, `python tests/e2e_checkout.py`.
- [ ] **Grafana SLOs**
  - Dashboards: API latency, DB queries, EC2 CPU, Nginx errors.
  - Alerts: Latency >500ms, uptime <99.9%.
- [ ] **Verify Sites**
  - https://staging.fazio.live (EC2).
  - https://fazio.live (EKS).
- **JD Skills**: Testing (pytest/Selenium), monitoring, communication (README).

### Day 7: Interview Prep
- [ ] **Demo**
  - Share: fazio.live, staging.fazio.live, grafana.fazio.live (read-only).
  - Screenshots: GitHub Actions, Grafana.
- [ ] **Cover JD**
  - **Jenkins**: Plan EC2 pipeline.
  - **CodePipeline**: Plan CodeBuild/CodeDeploy.
  - **SpringBoot**: Plan ECS microservice.
  - **ECS/Fargate**: Workers.
  - **Lambda/S3**: Webhooks, assets.
  - Prep answers:
    - CI/CD: “GitHub Actions automates tests, deploys to EC2/EKS.”
    - AWS: “EKS for prod, EC2 for staging, monitored with CloudWatch.”
    - Monitoring: “Prometheus/Grafana for SLOs, X-Ray for traces.”
- [ ] **Continuous Learning**
  - Keep repo: Add Jenkins, SpringBoot, chaos engineering later.
- **JD Skills**: Jenkins, CodePipeline, SpringBoot, ECS, Fargate, Lambda, S3, soft skills.

## Notes
- **AWS Costs**: ~$20-30 (EC2, EKS, Route 53). Shut down post-interview.
- **PDF**: Save this as `README.md`, convert to PDF:
  - VS Code: Install “Markdown PDF” extension → Export.
  - Online: Use pandoc (`pandoc README.md -o README.pdf`).
- **Help**: Errors? Share details (e.g., Terraform output).

## Status
- [ ] Day 1 Complete
- [ ] Day 2 Complete
- [ ] Day 3 Complete
- [ ] Day 4 Complete
- [ ] Day 5 Complete
- [ ] Day 6 Complete
- [ ] Day 7 Complete
```
