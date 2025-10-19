# Python Monitoring System
# Author Vladyslav Stadnyk

A comprehensive monitoring system built with Python, Prometheus, and Grafana for system metrics, web service monitoring, and alerting.

## 🚀 Features

- **System Monitoring**: CPU, memory, disk usage, and load average
- **Web Service Monitoring**: Uptime, response time, HTTP status codes
- **Real-time Dashboard**: Web interface with live metrics and charts
- **Prometheus Integration**: Exports metrics for Prometheus collection
- **Grafana Dashboards**: Pre-configured dashboards for visualization
- **Alerting System**: Email notifications based on configurable thresholds
- **Docker Support**: Fully containerized with Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose
- Git

## 🛠️ Quick Start

### 1. Clone the repository
```bash
git clone <repository-url>
cd monitoring-system
```

### 2. Start the monitoring system
```bash
docker-compose up -d
```

### 3. Access the services
- **Python Dashboard**: http://localhost:5001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Node Exporter**: http://localhost:9100

## 📊 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| `monitor` | 8000 | Python monitoring script with Prometheus metrics |
| `dashboard` | 5001 | Flask web dashboard |
| `prometheus` | 9090 | Metrics collection and storage |
| `grafana` | 3000 | Visualization and dashboards |
| `node-exporter` | 9100 | System metrics exporter |

## 🔧 Configuration

### Monitor Configuration (`monitor_config.json`)
```json
{
  "check_interval": 60,
  "cpu_threshold": 80,
  "memory_threshold": 85,
  "disk_threshold": 90,
  "email_alerts": false,
  "web_endpoints": [
    {
      "name": "Main App",
      "url": "http://localhost:8000/health"
    }
  ]
}
```

### Prometheus Configuration (`prometheus.yml`)
- Scrapes metrics from all services
- 15-second collection interval
- 200-hour data retention

## 📈 API Endpoints

### Dashboard API
- `GET /api/metrics/current` - Current system metrics
- `GET /api/metrics/history` - Historical metrics data
- `GET /api/web/status` - Web service status
- `GET /api/alerts` - Active alerts

### Prometheus Metrics
- `GET /metrics` - Prometheus-formatted metrics from monitor service

## 🎯 Usage Examples

### Check system health
```bash
curl http://localhost:5001/api/metrics/current
```

### View web service status
```bash
curl http://localhost:5001/api/web/status
```

### Access Prometheus metrics
```bash
curl http://localhost:8000/metrics
```

## 📊 Grafana Dashboards

### Available Dashboards
1. **Node Exporter Full** - System metrics (CPU, memory, disk, network)
2. **Prometheus Stats** - Prometheus server metrics
3. **Custom Python Metrics** - Application-specific metrics

### Setting up Grafana
1. Open http://localhost:3000
2. Login with admin/admin
3. Go to Dashboards
4. Select "Node Exporter Full" for system metrics

## 🔍 Monitoring Capabilities

### System Metrics
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Load average
- Network statistics

### Web Service Monitoring
- HTTP response codes
- Response times
- Uptime tracking
- Error detection

### Alerting
- Configurable thresholds
- Email notifications
- Real-time alerting
- Historical alert tracking

## 🐳 Docker Commands

### Start services
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f [service-name]
```

### Stop services
```bash
docker-compose down
```

### Rebuild services
```bash
docker-compose build
docker-compose up -d
```

## 📁 Project Structure

```
monitoring-system/
├── monitor.py              # Main monitoring script
├── dashboard.py            # Flask web dashboard
├── monitor_config.json     # Configuration file
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker services
├── Dockerfile             # Python app container
├── prometheus.yml         # Prometheus configuration
└── templates/
    └── dashboard.html     # Web dashboard template
```

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run monitor script
python monitor.py

# Run dashboard
python dashboard.py
```

### Adding New Metrics
1. Modify `monitor.py` to collect new metrics
2. Update Prometheus configuration if needed
3. Add visualization in Grafana

## 📝 Configuration Options

### Monitor Settings
- `check_interval`: Monitoring frequency in seconds
- `cpu_threshold`: CPU alert threshold percentage
- `memory_threshold`: Memory alert threshold percentage
- `disk_threshold`: Disk alert threshold percentage
- `email_alerts`: Enable/disable email notifications

### Web Endpoints
Add services to monitor by updating the `web_endpoints` array in `monitor_config.json`.

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 3000, 5001, 8000, 9090, 9100 are available
2. **Database errors**: Ensure the `data/` directory is writable
3. **Prometheus targets down**: Check service connectivity and configuration

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs monitor
docker-compose logs dashboard
```

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ using Python, Prometheus, and Grafana**