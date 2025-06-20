# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Invoice Reimbursement System to production for Flutter frontend integration.

## 🚀 Production Readiness Features

### Security Features

- ✅ Security headers middleware (XSS, CSRF, etc.)
- ✅ Rate limiting per client IP
- ✅ CORS configuration for specific origins
- ✅ Input validation and sanitization
- ✅ Request size limits
- ✅ Environment-based configuration

### API Features

- ✅ Standardized error responses
- ✅ Request ID tracking
- ✅ Comprehensive health checks
- ✅ Structured logging
- ✅ Streaming responses for real-time updates

### Monitoring Features

- ✅ Health check endpoints (`/api/v1/health`, `/api/v1/health/quick`)
- ✅ Service-specific health checks
- ✅ Detailed error logging
- ✅ Request/response tracking

## 🛠️ Pre-Production Checklist

### 1. Environment Configuration

```bash
# Copy production environment template
cp .env.production .env

# Configure required variables:
# - GOOGLE_API_KEY (Gemini API key)
# - SECRET_KEY (32+ character secure key)
# - ALLOWED_HOSTS (your Flutter app domains)
# - QDRANT_URL (production Qdrant instance)
# - QDRANT_API_KEY (if using Qdrant Cloud)
```

### 2. Security Configuration

- [ ] Set `DEBUG=False`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `ALLOWED_HOSTS` with your Flutter app domains
- [ ] Generate secure `SECRET_KEY` (minimum 32 characters)
- [ ] Set up JWT authentication if needed
- [ ] Configure rate limiting based on your needs

### 3. Database Setup

```bash
# Option 1: Use Qdrant Cloud (Recommended for production)
# Sign up at https://qdrant.tech/
# Update QDRANT_URL and QDRANT_API_KEY in .env

# Option 2: Self-hosted Qdrant with Docker
docker run -d \
  --name qdrant-prod \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### 4. SSL/TLS Configuration

- [ ] Obtain SSL certificate for your domain
- [ ] Configure reverse proxy (nginx/Apache) with HTTPS
- [ ] Update ALLOWED_HOSTS to include HTTPS domains
- [ ] Test HTTPS connectivity

## 🌐 Production Deployment Options

### Option 1: Docker Deployment

1. **Create Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create docker-compose.yml:**

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    depends_on:
      - qdrant
    
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

3. **Deploy:**

```bash
docker-compose up -d
```

### Option 2: Cloud Platform Deployment

#### Heroku

```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret
# ... set other environment variables
git push heroku main
```

#### Railway

```bash
# Install Railway CLI
railway login
railway init
railway add
# Configure environment variables in Railway dashboard
railway deploy
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy invoice-reimbursement \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 3: VPS/Server Deployment

1. **Install dependencies:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Create app user
sudo useradd -m -s /bin/bash appuser
sudo -u appuser -H bash
```

2. **Setup application:**

```bash
cd /home/appuser
git clone your-repo
cd invoice-reimbursement
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create systemd service:**

```ini
# /etc/systemd/system/invoice-reimbursement.service
[Unit]
Description=Invoice Reimbursement API
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/home/appuser/invoice-reimbursement
Environment=PATH=/home/appuser/invoice-reimbursement/venv/bin
ExecStart=/home/appuser/invoice-reimbursement/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Configure nginx:**

```nginx
# /etc/nginx/sites-available/invoice-reimbursement
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For streaming responses
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

5. **Start services:**

```bash
sudo systemctl enable invoice-reimbursement
sudo systemctl start invoice-reimbursement
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## 📱 Flutter Frontend Integration

### 1. API Endpoints for Flutter

Your Flutter app can integrate with these endpoints:

```dart
// Base URL (replace with your production URL)
const String baseUrl = 'https://your-api-domain.com/api/v1';

// Health check
GET $baseUrl/health/quick

// Invoice analysis (with file uploads)
POST $baseUrl/analyze-invoices
Content-Type: multipart/form-data

// Streaming invoice analysis 
POST $baseUrl/analyze-invoices-stream
Accept: text/event-stream

// Chat with invoices
POST $baseUrl/chat
Content-Type: application/json

// Streaming chat
POST $baseUrl/chat/stream
Accept: text/event-stream

// Chat history
GET $baseUrl/chat/history/{session_id}
DELETE $baseUrl/chat/history/{session_id}
```

### 2. Flutter HTTP Client Setup

```dart
// http_client.dart
import 'package:dio/dio.dart';

class ApiClient {
  late Dio _dio;
  
  ApiClient() {
    _dio = Dio();
    _dio.options.baseUrl = 'https://your-api-domain.com/api/v1';
    _dio.options.connectTimeout = Duration(seconds: 30);
    _dio.options.receiveTimeout = Duration(seconds: 30);
    
    // Add interceptors for logging, auth, etc.
    _dio.interceptors.add(LogInterceptor());
  }
  
  // Upload invoices
  Future<Map<String, dynamic>> uploadInvoices({
    required String employeeName,
    required File policyFile,
    required File invoicesZip,
  }) async {
    FormData formData = FormData.fromMap({
      'employee_name': employeeName,
      'policy_file': await MultipartFile.fromFile(policyFile.path),
      'invoices_zip': await MultipartFile.fromFile(invoicesZip.path),
    });
    
    Response response = await _dio.post('/analyze-invoices', data: formData);
    return response.data;
  }
  
  // Chat with invoices
  Future<Map<String, dynamic>> chatWithInvoices({
    required String query,
    String? sessionId,
  }) async {
    Response response = await _dio.post('/chat', data: {
      'query': query,
      'session_id': sessionId,
      'include_sources': true,
    });
    return response.data;
  }
}
```

### 3. Server-Sent Events for Streaming

```dart
// streaming_service.dart
import 'package:http/http.dart' as http;

class StreamingService {
  Stream<Map<String, dynamic>> streamInvoiceAnalysis({
    required String employeeName,
    required File policyFile,
    required File invoicesZip,
  }) async* {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/analyze-invoices-stream'),
    );
    
    request.fields['employee_name'] = employeeName;
    request.files.add(await http.MultipartFile.fromPath('policy_file', policyFile.path));
    request.files.add(await http.MultipartFile.fromPath('invoices_zip', invoicesZip.path));
    
    final response = await request.send();
    
    await for (String line in response.stream.transform(utf8.decoder).transform(LineSplitter())) {
      if (line.startsWith('data: ')) {
        final jsonData = line.substring(6);
        if (jsonData.trim().isNotEmpty) {
          yield json.decode(jsonData);
        }
      }
    }
  }
}
```

## 🔍 Monitoring and Maintenance

### Health Check Monitoring

```bash
# Set up monitoring (example with curl)
curl -f https://your-api-domain.com/api/v1/health/quick || echo "API is down"

# Detailed health check
curl https://your-api-domain.com/api/v1/health
```

### Log Monitoring

```bash
# Monitor application logs
tail -f logs/app_$(date +%Y%m%d).log

# Search for errors
grep -i error logs/app_*.log
```

### Performance Monitoring

- Monitor response times for each endpoint
- Track rate limiting effectiveness
- Monitor memory and CPU usage
- Set up alerts for service failures

## 🔧 Troubleshooting

### Common Issues

1. **CORS errors from Flutter:**
   - Verify `ALLOWED_HOSTS` includes your Flutter app domains
   - Check that origins are properly configured

2. **File upload failures:**
   - Check file size limits (`MAX_FILE_SIZE`)
   - Verify file types are allowed (`ALLOWED_EXTENSIONS`)
   - Ensure upload directory has write permissions

3. **Vector store connection issues:**
   - Verify Qdrant is running and accessible
   - Check network connectivity and firewall rules
   - Validate API credentials for cloud instances

4. **LLM service failures:**
   - Verify Google API key is valid and has quota
   - Check network connectivity to Google APIs
   - Monitor rate limiting and usage quotas

### Support

- Check logs in `logs/` directory
- Use health check endpoints for diagnostics
- Monitor application metrics and alerts
- Review error responses with request IDs for tracking

---

## ✅ Production Launch Checklist

- [ ] Environment variables configured correctly
- [ ] SSL certificate installed and working
- [ ] Domain DNS configured
- [ ] Health checks passing
- [ ] Rate limiting tested
- [ ] File upload limits tested
- [ ] CORS configuration verified with Flutter app
- [ ] Logging and monitoring set up
- [ ] Backup and recovery procedures tested
- [ ] Load testing completed
- [ ] Security review completed

Your Invoice Reimbursement System is now production-ready for Flutter frontend integration! 🎉
