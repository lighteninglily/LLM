#!/bin/bash
#
# Setup Monitoring Dashboard for LLM Server
# Installs and configures Grafana + Prometheus for monitoring
#
# Usage:
#   sudo ./setup-monitoring.sh
#

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "================================================================"
echo "  LLM Server Monitoring Setup"
echo "================================================================"
echo ""

# Install Prometheus
log_info "Installing Prometheus..."
apt-get update
apt-get install -y prometheus prometheus-node-exporter

# Configure Prometheus for Docker
log_info "Configuring Prometheus..."
cat > /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
  
  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9323']
  
  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['localhost:9445']
EOF

systemctl restart prometheus
systemctl enable prometheus

# Install Grafana
log_info "Installing Grafana..."
apt-get install -y software-properties-common
add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
apt-get update
apt-get install -y grafana

systemctl start grafana-server
systemctl enable grafana-server

# Install NVIDIA GPU exporter
log_info "Installing NVIDIA GPU exporter..."
wget https://github.com/utkuozdemir/nvidia_gpu_exporter/releases/latest/download/nvidia_gpu_exporter_linux_amd64.tar.gz
tar -xzf nvidia_gpu_exporter_linux_amd64.tar.gz
mv nvidia_gpu_exporter /usr/local/bin/
rm nvidia_gpu_exporter_linux_amd64.tar.gz

# Create systemd service for GPU exporter
cat > /etc/systemd/system/nvidia-gpu-exporter.service << 'EOF'
[Unit]
Description=NVIDIA GPU Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/nvidia_gpu_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start nvidia-gpu-exporter
systemctl enable nvidia-gpu-exporter

# Configure firewall
log_info "Configuring firewall..."
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus

# Create Grafana data source
log_info "Waiting for Grafana to start..."
sleep 10

# Configure Prometheus data source in Grafana
curl -X POST \
  http://admin:admin@localhost:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }' 2>/dev/null || true

# Create monitoring directory
mkdir -p ~/.local-ai-server/monitoring

# Create custom dashboard JSON
cat > ~/.local-ai-server/monitoring/llm-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "LLM Server Monitor",
    "panels": [
      {
        "title": "GPU Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "nvidia_gpu_utilization"
          }
        ]
      },
      {
        "title": "GPU Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "nvidia_gpu_memory_used_bytes"
          }
        ]
      },
      {
        "title": "GPU Temperature",
        "type": "graph",
        "targets": [
          {
            "expr": "nvidia_gpu_temperature_celsius"
          }
        ]
      },
      {
        "title": "Container CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m])"
          }
        ]
      },
      {
        "title": "Container Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "container_memory_usage_bytes"
          }
        ]
      }
    ]
  }
}
EOF

echo ""
echo "================================================================"
echo "  Monitoring Setup Complete"
echo "================================================================"
echo ""
echo "Access Grafana:"
echo "  URL: http://localhost:3000"
echo "  Username: admin"
echo "  Password: admin (change on first login)"
echo ""
echo "Prometheus:"
echo "  URL: http://localhost:9090"
echo ""
echo "Metrics available:"
echo "  - GPU utilization and memory"
echo "  - Container CPU and memory"
echo "  - System resources"
echo "  - Docker stats"
echo ""
echo "Next steps:"
echo "  1. Login to Grafana"
echo "  2. Change admin password"
echo "  3. Import dashboard from:"
echo "     ~/.local-ai-server/monitoring/llm-dashboard.json"
echo ""
