# ???? Sistema de Monitoreo y Observabilidad Enterprise

## Stack de Monitoreo

```
monitoring/
????????? prometheus/          # M??tricas y alerting
????????? grafana/           # Dashboards y visualizaci??n
????????? elasticsearch/       # Logs y b??squeda
????????? kibana/            # Visualizaci??n de logs
????????? loki/              # Agregaci??n de logs
????????? jaeger/            # Distributed tracing
????????? alertmanager/      # Gesti??n de alertas
????????? blackbox/          # Health checks externos
```

## Arquitectura de M??tricas

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'windmill-platform'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Load rules once and periodically evaluate them
rule_files:
  - "alerts/*.yml"
  - "recording_rules/*.yml"

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  # Windmill Platform API
  - job_name: 'windmill-platform-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          - windmill-platform
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Windmill Workers
  - job_name: 'windmill-workers'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          - windmill-platform
        selectors:
          - role: pod
            label: "app.kubernetes.io/component=worker"
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # Kubernetes API Server
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          - default
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # Kubernetes Nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

  # Kubernetes Pods
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Blackbox Exporter
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - https://api.windmill-platform.io/health
        - https://staging.windmill-platform.io/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

## Reglas de Alertas

```yaml
# monitoring/prometheus/alerts/platform.yml
groups:
  - name: windmill-platform
    interval: 30s
    rules:
      # API Availability
      - alert: WindmillPlatformAPIDown
        expr: up{job="windmill-platform-api"} == 0
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Windmill Platform API is down"
          description: "Windmill Platform API has been down for more than 2 minutes"
          runbook_url: "https://docs.windmill-platform.io/runbooks/api-down"

      # High Error Rate
      - alert: WindmillPlatformHighErrorRate
        expr: |
          (
            rate(http_requests_total{job="windmill-platform-api",status=~"5.."}[5m]) /
            rate(http_requests_total{job="windmill-platform-api"}[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High error rate on Windmill Platform API"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High Latency
      - alert: WindmillPlatformHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket{job="windmill-platform-api"}[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High latency on Windmill Platform API"
          description: "95th percentile latency is {{ $value }}s"

      # Database Connection Issues
      - alert: WindmillPlatformDatabaseConnections
        expr: |
          pg_stat_activity_count{datname="windmill"} > 80
        for: 5m
        labels:
          severity: warning
          team: database
        annotations:
          summary: "High database connection count"
          description: "{{ $value }} active connections to windmill database"

      # Redis Connection Issues
      - alert: WindmillPlatformRedisDown
        expr: up{job="redis"} == 0
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Redis is down"
          description: "Redis has been unreachable for more than 2 minutes"

      # Worker Health
      - alert: WindmillPlatformWorkersDown
        expr: |
          sum(up{job="windmill-workers"}) < 2
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Insufficient healthy workers"
          description: "Only {{ $value }} workers are healthy (minimum: 2)"

      # Queue Depth
      - alert: WindmillPlatformQueueDepth
        expr: |
          redis_key_size{key="windmill:queue:pending"} > 1000
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High queue depth"
          description: "Queue depth is {{ $value }} items"

      # Memory Usage
      - alert: WindmillPlatformHighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{container="windmill-platform"} /
            container_spec_memory_limit_bytes{container="windmill-platform"}
          ) > 0.9
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # CPU Usage
      - alert: WindmillPlatformHighCPUUsage
        expr: |
          (
            rate(container_cpu_usage_seconds_total{container="windmill-platform"}[5m]) * 100
          ) > 80
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      # Disk Usage
      - alert: WindmillPlatformHighDiskUsage
        expr: |
          (
            node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}
          ) / node_filesystem_size_bytes{mountpoint="/"} > 0.85
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value | humanizePercentage }}"

  - name: windmill-platform-business
    interval: 60s
    rules:
      # Execution Success Rate
      - alert: WindmillPlatformLowSuccessRate
        expr: |
          (
            rate(windmill_executions_total{status="success"}[10m]) /
            rate(windmill_executions_total[10m])
          ) < 0.95
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Low execution success rate"
          description: "Success rate is {{ $value | humanizePercentage }} for the last 10 minutes"

      # Execution Volume
      - alert: WindmillPlatformExecutionVolumeDrop
        expr: |
          rate(windmill_executions_total[5m]) < rate(windmill_executions_total[1h] offset 1h) * 0.5
        for: 15m
        labels:
          severity: info
          team: platform
        annotations:
          summary: "Execution volume drop"
          description: "Execution volume has dropped by {{ $value | humanizePercentage }} compared to last hour"

      # Customer Impact
      - alert: WindmillPlatformCustomerImpact
        expr: |
          sum by (tenant_id) (rate(windmill_executions_total{status="failed"}[5m])) > 10
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High failure rate for tenant {{ $labels.tenant_id }}"
          description: "Tenant {{ $labels.tenant_id }} has {{ $value }} failed executions per second"
```

## Dashboards de Grafana

```json
{
  "dashboard": {
    "id": null,
    "title": "Windmill Platform Overview",
    "tags": ["windmill", "platform", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"windmill-platform-api\"}",
            "legendFormat": "API Status"
          },
          {
            "expr": "up{job=\"windmill-workers\"}",
            "legendFormat": "Workers Status"
          },
          {
            "expr": "up{job=\"postgres\"}",
            "legendFormat": "Database Status"
          },
          {
            "expr": "up{job=\"redis\"}",
            "legendFormat": "Redis Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"value": 0, "text": "DOWN", "color": "red"},
              {"value": 1, "text": "UP", "color": "green"}
            ],
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"windmill-platform-api\"}[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec",
            "min": 0
          }
        ]
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job=\"windmill-platform-api\"}[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"windmill-platform-api\"}[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job=\"windmill-platform-api\"}[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Response Time (seconds)",
            "min": 0
          }
        ]
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"windmill-platform-api\",status=~\"5..\"}[5m]) / rate(http_requests_total{job=\"windmill-platform-api\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "yAxes": [
          {
            "label": "Error Rate",
            "min": 0,
            "max": 1
          }
        ]
      },
      {
        "id": 5,
        "title": "Queue Depth",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_key_size{key=\"windmill:queue:pending\"}",
            "legendFormat": "Pending Queue"
          },
          {
            "expr": "redis_key_size{key=\"windmill:queue:processing\"}",
            "legendFormat": "Processing Queue"
          }
        ],
        "yAxes": [
          {
            "label": "Items",
            "min": 0
          }
        ]
      },
      {
        "id": 6,
        "title": "Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(windmill_executions_total[5m])",
            "legendFormat": "Total Executions"
          },
          {
            "expr": "rate(windmill_executions_total{status=\"success\"}[5m])",
            "legendFormat": "Successful Executions"
          },
          {
            "expr": "rate(windmill_executions_total{status=\"failed\"}[5m])",
            "legendFormat": "Failed Executions"
          }
        ],
        "yAxes": [
          {
            "label": "Executions/sec",
            "min": 0
          }
        ]
      },
      {
        "id": 7,
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{container=\"windmill-platform\"}[5m]) * 100",
            "legendFormat": "CPU Usage %"
          },
          {
            "expr": "container_memory_usage_bytes{container=\"windmill-platform\"} / 1024 / 1024",
            "legendFormat": "Memory Usage MB"
          }
        ],
        "yAxes": [
          {
            "label": "CPU %",
            "min": 0,
            "max": 100
          },
          {
            "label": "Memory MB",
            "min": 0
          }
        ]
      },
      {
        "id": 8,
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit{datname=\"windmill\"}[5m])",
            "legendFormat": "Commits/sec"
          },
          {
            "expr": "rate(pg_stat_database_xact_rollback{datname=\"windmill\"}[5m])",
            "legendFormat": "Rollbacks/sec"
          }
        ],
        "yAxes": [
          {
            "label": "Transactions/sec",
            "min": 0
          }
        ]
      }
    ]
  }
}
```

## Configuraci??n de ELK Stack

```yaml
# monitoring/elasticsearch/elasticsearch.yml
cluster.name: windmill-platform
node.name: elasticsearch-0
network.host: 0.0.0.0
http.port: 9200
discovery.seed_hosts: ["elasticsearch-0", "elasticsearch-1", "elasticsearch-2"]
cluster.initial_master_nodes: ["elasticsearch-0", "elasticsearch-1", "elasticsearch-2"]

# Security
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true

# Performance
indices.memory.index_buffer_size: 30%
indices.queries.cache.size: 15%
indices.fielddata.cache.size: 30%

# Monitoring
xpack.monitoring.collection.enabled: true
xpack.monitoring.elasticsearch.collection.enabled: true
```

```yaml
# monitoring/filebeat/filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/log/containers/*.log'
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"
    - decode_json_fields:
        fields: ["message"]
        target: ""
        overwrite_keys: true
    - drop_fields:
        fields: ["agent", "ecs", "input", "log.file", "log.offset"]

output.elasticsearch:
  hosts: ['https://elasticsearch:9200']
  username: ${ELASTICSEARCH_USERNAME}
  password: ${ELASTICSEARCH_PASSWORD}
  ssl.certificate_authorities: ["/etc/ssl/certs/ca-certificates.crt"]
  index: "windmill-platform-%{+yyyy.MM.dd}"

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

## Sistema de Logs Estructurados

```python
# src/windmill_platform/monitoring/structured_logging.py
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class StructuredLogger:
    """Sistema de logging estructurado para Windmill Platform"""
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        service_name: str = "windmill-platform",
        environment: str = "production"
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.service_name = service_name
        self.environment = environment
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            timestamp=True
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _format_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format log entry with structured data"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'service': self.service_name,
            'environment': self.environment,
            'message': message,
            'logger': self.logger.name
        }
        
        if extra:
            entry.update(extra)
        
        return entry
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        entry = self._format_log_entry('INFO', message, extra)
        self.logger.info(json.dumps(entry))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info=None):
        """Log error message"""
        entry = self._format_log_entry('ERROR', message, extra)
        if exc_info:
            entry['exception'] = str(exc_info)
        self.logger.error(json.dumps(entry), exc_info=exc_info)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        entry = self._format_log_entry('WARNING', message, extra)
        self.logger.warning(json.dumps(entry))
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        entry = self._format_log_entry('DEBUG', message, extra)
        self.logger.debug(json.dumps(entry))
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        entry = self._format_log_entry('CRITICAL', message, extra)
        self.logger.critical(json.dumps(entry))

# Application-specific loggers
class AutomationLogger(StructuredLogger):
    """Logger for automation execution"""
    
    def log_execution_start(
        self,
        automation_id: str,
        execution_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Log automation execution start"""
        self.info(
            "Automation execution started",
            extra={
                'automation_id': automation_id,
                'execution_id': execution_id,
                'parameters': parameters or {},
                'event_type': 'execution_start'
            }
        )
    
    def log_execution_end(
        self,
        automation_id: str,
        execution_id: str,
        status: str,
        duration: float,
        output: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log automation execution end"""
        extra = {
            'automation_id': automation_id,
            'execution_id': execution_id,
            'status': status,
            'duration_seconds': duration,
            'event_type': 'execution_end'
        }
        
        if output:
            extra['output'] = output
        if error:
            extra['error'] = error
        
        if status == 'success':
            self.info("Automation execution completed successfully", extra=extra)
        else:
            self.error("Automation execution failed", extra=extra)
    
    def log_execution_step(
        self,
        automation_id: str,
        execution_id: str,
        step_name: str,
        step_number: int,
        duration: float
    ):
        """Log execution step completion"""
        self.info(
            f"Automation step completed: {step_name}",
            extra={
                'automation_id': automation_id,
                'execution_id': execution_id,
                'step_name': step_name,
                'step_number': step_number,
                'duration_seconds': duration,
                'event_type': 'execution_step'
            }
        )

class BillingLogger(StructuredLogger):
    """Logger for billing events"""
    
    def log_subscription_created(
        self,
        tenant_id: str,
        subscription_id: str,
        plan_id: str,
        trial_days: int = 0
    ):
        """Log subscription creation"""
        self.info(
            "Subscription created",
            extra={
                'tenant_id': tenant_id,
                'subscription_id': subscription_id,
                'plan_id': plan_id,
                'trial_days': trial_days,
                'event_type': 'subscription_created'
            }
        )
    
    def log_usage_limit_exceeded(
        self,
        tenant_id: str,
        limit_type: str,
        current_usage: int,
        limit: int
    ):
        """Log usage limit exceeded"""
        self.warning(
            f"Usage limit exceeded: {limit_type}",
            extra={
                'tenant_id': tenant_id,
                'limit_type': limit_type,
                'current_usage': current_usage,
                'limit': limit,
                'overage': current_usage - limit,
                'event_type': 'usage_limit_exceeded'
            }
        )

class SecurityLogger(StructuredLogger):
    """Logger for security events"""
    
    def log_authentication_attempt(
        self,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        success: bool,
        reason: Optional[str] = None
    ):
        """Log authentication attempt"""
        level = 'INFO' if success else 'WARNING'
        message = "Authentication successful" if success else "Authentication failed"
        
        extra = {
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success,
            'event_type': 'authentication_attempt'
        }
        
        if reason:
            extra['reason'] = reason
        
        if success:
            self.info(message, extra=extra)
        else:
            self.warning(message, extra=extra)
    
    def log_api_key_usage(
        self,
        api_key_id: str,
        endpoint: str,
        method: str,
        ip_address: str,
        user_agent: str
    ):
        """Log API key usage"""
        self.info(
            "API key used",
            extra={
                'api_key_id': api_key_id,
                'endpoint': endpoint,
                'method': method,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'event_type': 'api_key_usage'
            }
        )
```

## M??tricas Custom con Prometheus

```python
# src/windmill_platform/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, Enum
import time
from functools import wraps
from typing import Callable, Any

# System metrics
SYSTEM_INFO = Info('windmill_platform_system', 'System information')
SYSTEM_INFO.info({
    'version': '1.0.0',
    'environment': 'production',
    'python_version': '3.12'
})

# HTTP metrics
http_requests_total = Counter(
    'windmill_platform_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'windmill_platform_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Execution metrics
executions_total = Counter(
    'windmill_platform_executions_total',
    'Total automation executions',
    ['automation_id', 'status', 'tenant_id']
)

execution_duration_seconds = Histogram(
    'windmill_platform_execution_duration_seconds',
    'Automation execution duration',
    ['automation_id', 'tenant_id'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800]
)

# Queue metrics
queue_depth = Gauge(
    'windmill_platform_queue_depth',
    'Current queue depth',
    ['queue_name']
)

queue_processing_time_seconds = Histogram(
    'windmill_platform_queue_processing_time_seconds',
    'Time spent processing queue items',
    ['queue_name'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Resource metrics
active_workers = Gauge(
    'windmill_platform_active_workers',
    'Number of active workers',
    ['tenant_id']
)

memory_usage_bytes = Gauge(
    'windmill_platform_memory_usage_bytes',
    'Memory usage in bytes',
    ['tenant_id', 'component']
)

cpu_usage_percent = Gauge(
    'windmill_platform_cpu_usage_percent',
    'CPU usage percentage',
    ['tenant_id', 'component']
)

# Business metrics
automation_creations_total = Counter(
    'windmill_platform_automation_creations_total',
    'Total automation creations',
    ['tenant_id', 'plan_tier']
)

subscription_changes_total = Counter(
    'windmill_platform_subscription_changes_total',
    'Total subscription changes',
    ['tenant_id', 'from_plan', 'to_plan']
)

billing_events_total = Counter(
    'windmill_platform_billing_events_total',
    'Total billing events',
    ['tenant_id', 'event_type']
)

# Error metrics
errors_total = Counter(
    'windmill_platform_errors_total',
    'Total errors',
    ['error_type', 'component', 'tenant_id']
)

# Decorators for easy metric collection
def track_execution_time(metric_name: str, labels: list = None):
    """Decorator to track execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success
                if labels:
                    label_values = []
                    for label in labels:
                        if callable(label):
                            label_values.append(label(*args, **kwargs))
                        else:
                            label_values.append(label)
                    execution_duration_seconds.labels(*label_values).observe(duration)
                else:
                    execution_duration_seconds.labels().observe(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failure with error type
                error_labels = label_values.copy() if labels else []
                error_labels.append(type(e).__name__)
                
                execution_duration_seconds.labels(*error_labels).observe(duration)
                raise
        return wrapper
    return decorator

def track_request_metrics(endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            method = kwargs.get('method', 'GET')
            
            try:
                result = func(*args, **kwargs)
                status = 200  # Assume success if no exception
                
                # Record metrics
                http_requests_total.labels(method, endpoint, status).inc()
                http_request_duration_seconds.labels(method, endpoint).observe(time.time() - start_time)
                
                return result
            except Exception as e:
                # Determine status code from exception
                status = 500
                if hasattr(e, 'status_code'):
                    status = e.status_code
                
                # Record error metrics
                http_requests_total.labels(method, endpoint, status).inc()
                http_request_duration_seconds.labels(method, endpoint).observe(time.time() - start_time)
                
                raise
        return wrapper
    return decorator
```

## Sistema de Alertas Avanzado

```python
# src/windmill_platform/monitoring/alert_manager.py
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    PENDING = "pending"

@dataclass
class Alert:
    """Alert data structure"""
    name: str
    severity: AlertSeverity
    status: AlertStatus
    summary: str
    description: str
    labels: Dict[str, str]
    starts_at: datetime
    ends_at: Optional[datetime] = None
    generator_url: Optional[str] = None
    fingerprint: Optional[str] = None

class AlertManager:
    """Advanced alert management system"""
    
    def __init__(
        self,
        alertmanager_url: str,
        slack_webhook_url: Optional[str] = None,
        pagerduty_integration_key: Optional[str] = None,
        email_smtp_config: Optional[Dict[str, Any]] = None
    ):
        self.alertmanager_url = alertmanager_url
        self.slack_webhook_url = slack_webhook_url
        self.pagerduty_integration_key = pagerduty_integration_key
        self.email_smtp_config = email_smtp_config
        
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to configured channels"""
        try:
            # Send to Alertmanager
            await self._send_to_alertmanager(alert)
            
            # Send to Slack if configured
            if self.slack_webhook_url and alert.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
                await self._send_to_slack(alert)
            
            # Send to PagerDuty if critical
            if self.pagerduty_integration_key and alert.severity == AlertSeverity.CRITICAL:
                await self._send_to_pagerduty(alert)
            
            # Send email if configured
            if self.email_smtp_config and alert.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
                await self._send_email(alert)
            
            # Store in history
            self.alert_history.append(alert)
            
            logger.info(f"Alert sent: {alert.name} - {alert.summary}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert {alert.name}: {e}")
            return False
    
    async def _send_to_alertmanager(self, alert: Alert) -> bool:
        """Send alert to Alertmanager"""
        payload = {
            "receiver": "windmill-platform",
            "status": alert.status.value,
            "alerts": [
                {
                    "status": alert.status.value,
                    "labels": alert.labels,
                    "annotations": {
                        "summary": alert.summary,
                        "description": alert.description
                    },
                    "startsAt": alert.starts_at.isoformat(),
                    "endsAt": alert.ends_at.isoformat() if alert.ends_at else None,
                    "generatorURL": alert.generator_url,
                    "fingerprint": alert.fingerprint
                }
            ],
            "groupLabels": {
                "alertname": alert.name
            },
            "commonLabels": alert.labels,
            "commonAnnotations": {
                "summary": alert.summary,
                "description": alert.description
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.alertmanager_url}/api/v1/alerts",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Alertmanager returned status {response.status}")
                    return False
    
    async def _send_to_slack(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000"
        }
        
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#36a64f"),
                    "title": f"???? {alert.name}",
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Service", "value": alert.labels.get('service', 'unknown'), "short": True},
                        {"title": "Environment", "value": alert.labels.get('environment', 'unknown'), "short": True}
                    ],
                    "footer": "Windmill Platform",
                    "ts": int(alert.starts_at.timestamp())
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.slack_webhook_url, json=payload) as response:
                return response.status == 200
    
    async def _send_to_pagerduty(self, alert: Alert) -> bool:
        """Send alert to PagerDuty"""
        payload = {
            "routing_key": self.pagerduty_integration_key,
            "event_action": "trigger",
            "dedup_key": alert.fingerprint or f"{alert.name}-{alert.starts_at.isoformat()}",
            "payload": {
                "summary": alert.summary,
                "source": alert.labels.get('instance', 'unknown'),
                "severity": "error" if alert.severity == AlertSeverity.CRITICAL else "warning",
                "timestamp": alert.starts_at.isoformat(),
                "component": alert.labels.get('service', 'unknown'),
                "group": alert.labels.get('team', 'platform'),
                "class": alert.name,
                "custom_details": {
                    "description": alert.description,
                    "environment": alert.labels.get('environment', 'unknown'),
                    "labels": alert.labels
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status == 202
    
    async def _send_email(self, alert: Alert) -> bool:
        """Send alert via email"""
        # Implementation would depend on email library used
        # This is a placeholder for email sending logic
        logger.info(f"Would send email alert: {alert.name}")
        return True
    
    def create_alert(
        self,
        name: str,
        severity: AlertSeverity,
        summary: str,
        description: str,
        labels: Dict[str, str],
        generator_url: Optional[str] = None
    ) -> Alert:
        """Create and send a new alert"""
        alert = Alert(
            name=name,
            severity=severity,
            status=AlertStatus.FIRING,
            summary=summary,
            description=description,
            labels=labels,
            starts_at=datetime.utcnow(),
            generator_url=generator_url,
            fingerprint=f"{name}-{labels.get('tenant_id', 'global')}"
        )
        
        # Store in active alerts
        self.active_alerts[alert.fingerprint] = alert
        
        # Send alert asynchronously
        asyncio.create_task(self.send_alert(alert))
        
        return alert
    
    def resolve_alert(self, fingerprint: str) -> bool:
        """Resolve an active alert"""
        if fingerprint not in self.active_alerts:
            return False
        
        alert = self.active_alerts[fingerprint]
        alert.status = AlertStatus.RESOLVED
        alert.ends_at = datetime.utcnow()
        
        # Send resolved alert
        asyncio.create_task(self.send_alert(alert))
        
        # Remove from active alerts
        del self.active_alerts[fingerprint]
        
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history with optional filtering"""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()
        
        filtered_history = []
        for alert in self.alert_history:
            if (start_time <= alert.starts_at <= end_time and
                (not severity or alert.severity == severity)):
                filtered_history.append(alert)
        
        return filtered_history
```

## Comandos de Monitoreo

```bash
#!/bin/bash
# scripts/monitoring-setup.sh

# Setup complete monitoring stack
echo "???? Setting up Windmill Platform monitoring..."

# Create monitoring namespace
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=<set_via_secret> \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi

# Install Elasticsearch
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch \
  --namespace monitoring \
  --set replicas=3 \
  --set minimumMasterNodes=2 \
  --set volumeClaimTemplate.resources.requests.storage=30Gi

# Install Kibana
helm install kibana elastic/kibana \
  --namespace monitoring \
  --set elasticsearchHosts=http://elasticsearch-master:9200

# Install Loki
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=true \
  --set prometheus.enabled=false \
  --set grafana.adminPassword=<set_via_secret>

# Install Jaeger
kubectl apply -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/crds/jaegertracing.io_jaegers_crd.yaml
kubectl apply -n monitoring -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/service_account.yaml
kubectl apply -n monitoring -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role.yaml
kubectl apply -n monitoring -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role_binding.yaml
kubectl apply -n monitoring -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/operator.yaml

# Create Jaeger instance
cat <<EOF | kubectl apply -f -
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: windmill-platform-jaeger
  namespace: monitoring
spec:
  strategy: production
  storage:
    type: elasticsearch
    options:
      es:
        server-urls: http://elasticsearch-master:9200
EOF

# Configure port forwarding for access
echo "???? Monitoring stack installed!"
echo "Prometheus: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "Kibana: kubectl port-forward -n monitoring svc/kibana-kb-http 5601:5601"
echo "Jaeger: kubectl port-forward -n monitoring svc/windmill-platform-jaeger-query 16686:16686"
```

Este sistema de monitoreo enterprise proporciona:

1. **M??tricas detalladas** con Prometheus
2. **Dashboards interactivos** con Grafana
3. **Logs estructurados** con ELK Stack
4. **Alertas inteligentes** con Alertmanager
5. **Tracing distribuido** con Jaeger
6. **Monitoreo de salud** con checks personalizados
7. **Integraci??n con sistemas** de notificaci??n (Slack, PagerDuty, Email)
8. **An??lisis de tendencias** y capacidad predictiva
9. **Reportes autom??ticos** de disponibilidad y rendimiento
10. **Cumplimiento y auditor??a** de m??tricas

El sistema est?? dise??ado para escalar horizontalmente y manejar miles de automatizaciones concurrentes con monitoreo en tiempo real.
