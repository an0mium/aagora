# Aragora Deployment Guide

Deploy the Aragora server to keep `aragora.ai` running 24/7.

## Quick Start (AWS Lightsail)

1. **Launch Instance**
   - Go to AWS Lightsail
   - Create Ubuntu 22.04 instance (1GB RAM minimum, 2GB recommended)
   - Select "Networking" and open ports: 80, 443, 8080, 8765

2. **Connect and Install**
   ```bash
   ssh ubuntu@your-instance-ip
   git clone https://github.com/yourusername/aragora.git
   cd aragora
   ./deploy/setup-server.sh
   ```

3. **Configure API Keys**
   ```bash
   sudo nano /opt/aragora/.env
   ```
   Add your keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-proj-...
   OPENROUTER_API_KEY=sk-or-...
   GEMINI_API_KEY=AIza...
   XAI_API_KEY=xai-...
   ```

4. **Configure Domain**
   ```bash
   sudo nano /etc/nginx/sites-available/aragora
   # Replace YOUR_DOMAIN with api.aragora.ai
   sudo certbot --nginx -d api.aragora.ai
   sudo systemctl restart aragora nginx
   ```

## Docker Deployment

For containerized deployment:

```bash
cd deploy
docker-compose up -d
```

## Management Commands

```bash
# Check status
sudo systemctl status aragora

# View logs
sudo journalctl -u aragora -f

# Restart server
sudo systemctl restart aragora

# Health check
curl http://localhost:8080/healthz
```

## Ports

| Port | Service | Description |
|------|---------|-------------|
| 80   | nginx   | HTTP (redirects to HTTPS) |
| 443  | nginx   | HTTPS |
| 8080 | aragora | HTTP API (internal) |
| 8765 | aragora | WebSocket (internal) |

## Monitoring

The server exposes health endpoints:
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe  
- `GET /api/health/detailed` - Detailed health

## SSL/TLS

Use Let's Encrypt for free SSL:
```bash
sudo certbot --nginx -d api.aragora.ai
```

## Troubleshooting

**Server won't start**
```bash
sudo journalctl -u aragora -n 100
python -m aragora doctor
```

**WebSocket fails** - Check ports 8765 open in security group

**API 500 errors** - Check .env keys, run doctor
