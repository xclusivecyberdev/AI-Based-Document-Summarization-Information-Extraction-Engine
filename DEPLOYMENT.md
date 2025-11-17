# Deployment Guide

## Production Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker installed
- Docker Compose installed
- Domain name (optional)
- SSL certificate (optional)

#### Steps

1. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd AI-Based-Document-Summarization-Information-Extraction-Engine

   # Create production .env
   cp .env.example .env
   nano .env
   ```

2. **Update Environment Variables**
   ```bash
   # .env
   ENVIRONMENT=production
   DEBUG=False
   SECRET_KEY=<generate-strong-secret-key>
   DATABASE_URL=postgresql://user:pass@db:5432/docai
   DEVICE=cuda  # if GPU available
   ```

3. **Build and Run**
   ```bash
   docker-compose up -d --build
   ```

4. **Verify**
   ```bash
   docker-compose logs -f
   curl http://localhost:8000/api/health
   ```

### Option 2: Manual Deployment with systemd

#### 1. Server Setup (Ubuntu 20.04/22.04)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3-pip python3-venv
sudo apt install -y tesseract-ocr poppler-utils
sudo apt install -y nginx postgresql

# Install Node.js (for additional features)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Application Setup

```bash
# Create app directory
sudo mkdir -p /opt/document-ai
cd /opt/document-ai

# Clone repository
sudo git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download models
python scripts/init_models.py

# Create directories
mkdir -p uploads processed logs
```

#### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE docai;
CREATE USER docai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE docai TO docai_user;
\q

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://docai_user:secure_password@localhost/docai
```

#### 4. Create systemd Service

```bash
sudo nano /etc/systemd/system/document-ai.service
```

```ini
[Unit]
Description=AI Document Platform
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/document-ai
Environment="PATH=/opt/document-ai/venv/bin"
ExecStart=/opt/document-ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable document-ai
sudo systemctl start document-ai
sudo systemctl status document-ai
```

#### 5. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/document-ai
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/document-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 6. SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl status certbot.timer
```

### Option 3: Kubernetes Deployment

#### 1. Create Kubernetes Manifests

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-ai
  template:
    metadata:
      labels:
        app: document-ai
    spec:
      containers:
      - name: document-ai
        image: your-registry/document-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: document-ai-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: document-ai-secrets
              key: secret-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        - name: processed
          mountPath: /app/processed
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
      - name: processed
        persistentVolumeClaim:
          claimName: processed-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: document-ai-service
spec:
  selector:
    app: document-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**secrets.yaml**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: document-ai-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:pass@postgres:5432/docai"
  secret-key: "your-secret-key"
```

#### 2. Deploy

```bash
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml

# Check status
kubectl get pods
kubectl get services
```

### Option 4: AWS Deployment

#### Using AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04
   - Type: t3.large (or larger)
   - Storage: 50GB
   - Security Group: Allow ports 22, 80, 443

2. **Install and Configure**
   ```bash
   ssh ubuntu@your-instance-ip

   # Follow Manual Deployment steps above
   ```

#### Using AWS ECS with Fargate

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name document-ai
   ```

2. **Build and Push Image**
   ```bash
   docker build -t document-ai .
   docker tag document-ai:latest <account-id>.dkr.ecr.region.amazonaws.com/document-ai:latest
   docker push <account-id>.dkr.ecr.region.amazonaws.com/document-ai:latest
   ```

3. **Create ECS Task Definition and Service**
   - Use AWS Console or CLI
   - Configure environment variables
   - Set up load balancer

### Option 5: Google Cloud Platform

#### Using Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/document-ai

# Deploy
gcloud run deploy document-ai \
  --image gcr.io/PROJECT_ID/document-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2
```

## Environment-Specific Configurations

### Production Settings

```python
# .env
ENVIRONMENT=production
DEBUG=False

# Security
SECRET_KEY=<64-character-random-string>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Performance
WORKERS=4
MAX_UPLOAD_SIZE=104857600  # 100MB
DEVICE=cuda  # if GPU available

# Logging
LOG_LEVEL=WARNING
```

### Staging Settings

```python
# .env
ENVIRONMENT=staging
DEBUG=False
SECRET_KEY=<staging-secret-key>
DATABASE_URL=postgresql://user:pass@staging-db:5432/dbname
WORKERS=2
```

## Monitoring and Logging

### 1. Application Logs

```bash
# View logs
sudo journalctl -u document-ai -f

# Docker logs
docker-compose logs -f
```

### 2. Setup Monitoring (Prometheus + Grafana)

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Error Tracking (Sentry)

```python
# Add to requirements.txt
sentry-sdk[fastapi]

# In app/main.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment=settings.ENVIRONMENT
)
```

## Backup and Recovery

### Database Backup

```bash
# Backup
pg_dump -h localhost -U docai_user docai > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U docai_user docai < backup.sql

# Automated backup (cron)
0 2 * * * /usr/bin/pg_dump -h localhost -U docai_user docai > /backups/db_$(date +\%Y\%m\%d).sql
```

### File Backup

```bash
# Backup uploads and processed files
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
tar -czf processed_backup_$(date +%Y%m%d).tar.gz processed/

# Sync to S3
aws s3 sync uploads/ s3://your-bucket/backups/uploads/
```

## Performance Optimization

### 1. Enable Gunicorn

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. Use Redis for Caching

```yaml
# docker-compose.yml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
```

### 3. CDN for Static Assets

- Use CloudFlare, AWS CloudFront, or similar
- Serve static files from CDN

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS (SSL/TLS)
- [ ] Enable firewall (UFW)
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Database access restrictions
- [ ] File upload validation
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity
- [ ] Use strong passwords
- [ ] Enable 2FA for admin accounts

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Permission denied:**
```bash
sudo chown -R www-data:www-data /opt/document-ai
sudo chmod -R 755 /opt/document-ai
```

**Database connection error:**
- Check DATABASE_URL
- Verify PostgreSQL is running
- Check firewall rules

**Out of memory:**
- Increase server RAM
- Reduce worker count
- Enable swap

## Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Deploy multiple instances
- Use shared storage (NFS, S3)
- Use external database (RDS, CloudSQL)

### Vertical Scaling
- Increase CPU/RAM
- Use GPU for faster processing
- Optimize database queries

## Support

For deployment issues:
- Check logs: `/var/log/document-ai/`
- GitHub Issues
- Email: support@example.com
