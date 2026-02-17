# 🚀 SDK y APIs de Integración Enterprise

## Arquitectura del SDK

```
sdk/
├── python/                 # SDK Python
│   ├── windmill_platform/
│   │   ├── __init__.py
│   │   ├── client.py      # Cliente principal
│   │   ├── models.py      # Modelos de datos
│   │   ├── exceptions.py  # Excepciones
│   │   ├── auth.py        # Autenticación
│   │   ├── automations.py # Gestión de automatizaciones
│   │   ├── billing.py     # Facturación
│   │   └── utils.py       # Utilidades
│   ├── tests/
│   ├── examples/
│   └── setup.py
├── javascript/             # SDK JavaScript/Node.js
├── go/                     # SDK Go
├── rust/                   # SDK Rust
└── java/                   # SDK Java
```

## SDK Python - Cliente Principal

```python
# sdk/python/windmill_platform/client.py
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin

from .models import (
    Automation, AutomationConfig, DeploymentResult,
    UsageMetrics, Subscription, Plan, ExecutionResult
)
from .exceptions import (
    WindmillPlatformError, AuthenticationError,
    RateLimitError, ValidationError, NotFoundError
)
from .auth import AuthManager
from .automations import AutomationManager
from .billing import BillingManager

logger = logging.getLogger(__name__)

class WindmillPlatformClient:
    """Cliente principal para Windmill Platform API"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.windmill-platform.io",
        timeout: int = 30,
        max_retries: int = 3,
        environment: str = "production"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.environment = environment
        
        # Initialize managers
        self.auth = AuthManager(api_key, base_url)
        self.automations = AutomationManager(self)
        self.billing = BillingManager(self)
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure HTTP session is created"""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': f'windmill-platform-sdk-python/1.0.0',
                    'X-Environment': self.environment
                }
            )
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        await self._ensure_session()
        
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(self.max_retries):
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    response_text = await response.text()
                    
                    if response.status == 429:
                        # Rate limit - wait and retry
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status >= 400:
                        error_data = {}
                        try:
                            error_data = await response.json()
                        except:
                            pass
                        
                        self._handle_error(response.status, error_data, response_text)
                    
                    try:
                        return await response.json()
                    except:
                        return {"status": "success", "data": response_text}
            
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise WindmillPlatformError(f"Request failed after {self.max_retries} attempts: {e}")
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        raise WindmillPlatformError("Max retries exceeded")
    
    def _handle_error(self, status_code: int, error_data: Dict[str, Any], response_text: str):
        """Handle API errors"""
        error_message = error_data.get('message', response_text)
        
        if status_code == 401:
            raise AuthenticationError(error_message)
        elif status_code == 404:
            raise NotFoundError(error_message)
        elif status_code == 422:
            raise ValidationError(error_message)
        else:
            raise WindmillPlatformError(f"API Error {status_code}: {error_message}")
    
    # Health and Status
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return await self._make_request('GET', '/health')
    
    async def get_status(self) -> Dict[str, Any]:
        """Get platform status"""
        return await self._make_request('GET', '/status')
    
    # Automation Management
    async def list_automations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Automation]:
        """List all automations"""
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        
        response = await self._make_request('GET', '/automations', params=params)
        return [Automation(**item) for item in response.get('data', [])]
    
    async def get_automation(self, automation_id: str) -> Automation:
        """Get automation by ID"""
        response = await self._make_request('GET', f'/automations/{automation_id}')
        return Automation(**response['data'])
    
    async def create_automation(self, config: AutomationConfig) -> Automation:
        """Create new automation"""
        response = await self._make_request(
            'POST',
            '/automations',
            json=config.dict()
        )
        return Automation(**response['data'])
    
    async def update_automation(
        self,
        automation_id: str,
        config: AutomationConfig
    ) -> Automation:
        """Update automation"""
        response = await self._make_request(
            'PUT',
            f'/automations/{automation_id}',
            json=config.dict()
        )
        return Automation(**response['data'])
    
    async def delete_automation(self, automation_id: str) -> bool:
        """Delete automation"""
        response = await self._make_request('DELETE', f'/automations/{automation_id}')
        return response.get('success', False)
    
    # Deployment
    async def deploy_automation(
        self,
        automation_id: str,
        environment: str = "production",
        wait: bool = True,
        timeout: int = 300
    ) -> DeploymentResult:
        """Deploy automation"""
        response = await self._make_request(
            'POST',
            f'/automations/{automation_id}/deploy',
            json={
                'environment': environment,
                'wait': wait,
                'timeout': timeout
            }
        )
        return DeploymentResult(**response['data'])
    
    async def get_deployment_status(self, deployment_id: str) -> DeploymentResult:
        """Get deployment status"""
        response = await self._make_request('GET', f'/deployments/{deployment_id}')
        return DeploymentResult(**response['data'])
    
    # Execution
    async def execute_automation(
        self,
        automation_id: str,
        parameters: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Execute automation manually"""
        response = await self._make_request(
            'POST',
            f'/automations/{automation_id}/execute',
            json={'parameters': parameters or {}}
        )
        return ExecutionResult(**response['data'])
    
    async def get_execution_status(self, execution_id: str) -> ExecutionResult:
        """Get execution status"""
        response = await self._make_request('GET', f'/executions/{execution_id}')
        return ExecutionResult(**response['data'])
    
    async def get_execution_logs(
        self,
        execution_id: str,
        tail: int = 100
    ) -> List[str]:
        """Get execution logs"""
        response = await self._make_request(
            'GET',
            f'/executions/{execution_id}/logs',
            params={'tail': tail}
        )
        return response.get('logs', [])
    
    # Scaling
    async def scale_automation(
        self,
        automation_id: str,
        workers: int,
        cpu: Optional[str] = None,
        memory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scale automation resources"""
        data = {'workers': workers}
        if cpu:
            data['cpu'] = cpu
        if memory:
            data['memory'] = memory
        
        return await self._make_request(
            'PUT',
            f'/automations/{automation_id}/scale',
            json=data
        )
    
    # Usage and Billing
    async def get_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UsageMetrics:
        """Get usage metrics"""
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        
        response = await self._make_request('GET', '/usage', params=params)
        return UsageMetrics(**response['data'])
    
    async def get_subscription(self) -> Subscription:
        """Get current subscription"""
        response = await self._make_request('GET', '/billing/subscription')
        return Subscription(**response['data'])
    
    async def get_plans(self) -> List[Plan]:
        """Get available plans"""
        response = await self._make_request('GET', '/billing/plans')
        return [Plan(**item) for item in response.get('data', [])]
    
    # Secrets Management
    async def list_secrets(self) -> List[Dict[str, Any]]:
        """List all secrets"""
        response = await self._make_request('GET', '/secrets')
        return response.get('data', [])
    
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret"""
        response = await self._make_request('GET', f'/secrets/{secret_name}')
        return response['data']
    
    async def create_secret(
        self,
        secret_name: str,
        secret_value: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create secret"""
        data = {
            'name': secret_name,
            'value': secret_value
        }
        if description:
            data['description'] = description
        
        response = await self._make_request('POST', '/secrets', json=data)
        return response['data']
    
    async def update_secret(
        self,
        secret_name: str,
        secret_value: str
    ) -> Dict[str, Any]:
        """Update secret"""
        response = await self._make_request(
            'PUT',
            f'/secrets/{secret_name}',
            json={'value': secret_value}
        )
        return response['data']
    
    async def delete_secret(self, secret_name: str) -> bool:
        """Delete secret"""
        response = await self._make_request('DELETE', f'/secrets/{secret_name}')
        return response.get('success', False)
    
    # Monitoring
    async def get_metrics(self) -> Dict[str, Any]:
        """Get platform metrics"""
        response = await self._make_request('GET', '/metrics')
        return response.get('data', {})
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        response = await self._make_request('GET', '/alerts')
        return response.get('data', [])
    
    # Webhooks
    async def create_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create webhook"""
        data = {
            'url': url,
            'events': events
        }
        if secret:
            data['secret'] = secret
        
        response = await self._make_request('POST', '/webhooks', json=data)
        return response['data']
    
    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """List webhooks"""
        response = await self._make_request('GET', '/webhooks')
        return response.get('data', [])
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook"""
        response = await self._make_request('DELETE', f'/webhooks/{webhook_id}')
        return response.get('success', False)

# Convenience sync client for simple operations
class SyncWindmillPlatformClient:
    """Synchronous wrapper for WindmillPlatformClient"""
    
    def __init__(self, *args, **kwargs):
        self._client = WindmillPlatformClient(*args, **kwargs)
        self._loop = None
    
    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._client.__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._loop:
            self._loop.run_until_complete(self._client.__aexit__(exc_type, exc_val, exc_tb))
            self._loop.close()
    
    def __getattr__(self, name):
        """Delegate all other methods to async client"""
        async_method = getattr(self._client, name)
        
        def sync_wrapper(*args, **kwargs):
            return self._loop.run_until_complete(async_method(*args, **kwargs))
        
        return sync_wrapper
```

## Modelos de Datos

```python
# sdk/python/windmill_platform/models.py
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class AutomationStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    DEPLOYING = "deploying"

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class PlanTier(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Base Models
class BaseWindmillModel(BaseModel):
    """Base model with common functionality"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AutomationConfig(BaseWindmillModel):
    """Automation configuration"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    template: Optional[str] = None
    code: Optional[str] = None
    language: str = Field("python", regex="^(python|javascript|typescript|go|rust)$")
    
    # Triggers
    schedule: Optional[str] = None  # Cron expression
    webhook: Optional[str] = None   # Webhook URL
    event: Optional[str] = None     # Event trigger
    
    # Resources
    cpu: str = Field("250m", regex="^[0-9]+m$")
    memory: str = Field("512Mi", regex="^[0-9]+(Mi|Gi)$")
    timeout: int = Field(300, ge=30, le=7200)  # 30 seconds to 2 hours
    
    # Environment
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    secrets: List[str] = Field(default_factory=list)
    
    # Dependencies
    requirements: List[str] = Field(default_factory=list)
    
    @validator('schedule')
    def validate_schedule(cls, v):
        if v and not cls._is_valid_cron(v):
            raise ValueError('Invalid cron expression')
        return v
    
    @staticmethod
    def _is_valid_cron(expression: str) -> bool:
        # Basic cron validation
        parts = expression.split()
        return len(parts) == 5 or len(parts) == 6

class Automation(BaseWindmillModel):
    """Automation model"""
    id: str
    name: str
    description: Optional[str]
    status: AutomationStatus
    config: AutomationConfig
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # Deployment info
    deployment_id: Optional[str] = None
    deployed_at: Optional[datetime] = None
    deployed_by: Optional[str] = None
    
    # Runtime info
    last_execution_at: Optional[datetime] = None
    execution_count: int = 0
    success_rate: float = 0.0

class DeploymentResult(BaseWindmillModel):
    """Deployment result"""
    deployment_id: str
    automation_id: str
    status: DeploymentStatus
    
    # Progress
    progress: float = 0.0
    steps_completed: int = 0
    total_steps: int = 0
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Resources
    deployed_resources: Dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseWindmillModel):
    """Execution result"""
    execution_id: str
    automation_id: str
    status: ExecutionStatus
    
    # Timing
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    output: Optional[str] = None
    error: Optional[str] = None
    return_code: Optional[int] = None
    
    # Resources used
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    
    # Logs
    logs: List[str] = Field(default_factory=list)

class UsageMetrics(BaseWindmillModel):
    """Usage metrics"""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    # Usage counts
    automations_created: int = 0
    executions_count: int = 0
    api_calls_count: int = 0
    storage_used_gb: float = 0.0
    workers_used: int = 0
    webhook_calls: int = 0
    
    # Performance metrics
    compute_time_seconds: int = 0
    avg_execution_time: float = 0.0
    success_rate: float = 0.0
    
    # Overages
    overage_automations: int = 0
    overage_executions: int = 0
    overage_api_calls: int = 0
    overage_cost: float = 0.0

class Plan(BaseWindmillModel):
    """Subscription plan"""
    id: str
    name: str
    description: str
    tier: PlanTier
    
    # Pricing
    price_monthly: int  # in cents
    price_yearly: int  # in cents
    
    # Limits
    max_automations: int
    max_executions_per_month: int
    max_workers: int
    max_storage_gb: int
    max_api_calls_per_month: int
    max_webhook_endpoints: int
    max_execution_time: int  # seconds
    max_concurrent_executions: int
    
    # Features
    priority_support: bool = False
    custom_integrations: bool = False
    advanced_monitoring: bool = False
    sla_guarantee: bool = False
    white_label: bool = False

class Subscription(BaseWindmillModel):
    """Subscription model"""
    id: str
    tenant_id: str
    plan_id: str
    
    # Status
    status: str  # active, canceled, past_due, unpaid, trialing
    
    # Billing
    stripe_subscription_id: Optional[str]
    stripe_customer_id: Optional[str]
    
    # Periods
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    
    # Control
    cancel_at_period_end: bool = False
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

# Integration Models
class WebhookEvent(BaseWindmillModel):
    """Webhook event"""
    id: str
    type: str
    automation_id: str
    
    # Event data
    data: Dict[str, Any]
    
    # Metadata
    timestamp: datetime
    retries: int = 0
    delivered: bool = False
    last_error: Optional[str] = None

class IntegrationConfig(BaseWindmillModel):
    """Integration configuration"""
    name: str
    type: str  # webhook, api, database, queue
    
    # Connection details
    url: Optional[str] = None
    method: Optional[str] = Field(None, regex="^(GET|POST|PUT|DELETE|PATCH)$")
    headers: Dict[str, str] = Field(default_factory=dict)
    
    # Authentication
    auth_type: Optional[str] = None  # bearer, basic, api_key
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Settings
    timeout: int = Field(30, ge=5, le=300)
    retry_attempts: int = Field(3, ge=0, le=10)
    retry_delay: int = Field(1, ge=0, le=60)

class ExecutionSchedule(BaseWindmillModel):
    """Execution schedule"""
    id: str
    automation_id: str
    
    # Schedule
    cron_expression: str
    timezone: str = "UTC"
    
    # Settings
    enabled: bool = True
    catch_up: bool = False  # Run missed executions
    max_concurrent: int = 1
    
    # Status
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
```

## Integraciones Pre-construidas

```python
# sdk/python/windmill_platform/integrations/crm.py
from typing import Dict, List, Optional, Any
from .base import BaseIntegration

class HubSpotIntegration(BaseIntegration):
    """HubSpot CRM Integration"""
    
    def __init__(self, api_key: str, client_id: Optional[str] = None):
        super().__init__("hubspot", {
            'api_key': api_key,
            'client_id': client_id
        })
    
    async def sync_contacts(self, automation_id: str) -> Dict[str, Any]:
        """Sync contacts from HubSpot"""
        return await self.execute_integration(automation_id, 'sync_contacts')
    
    async def create_contact(
        self,
        automation_id: str,
        contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create contact in HubSpot"""
        return await self.execute_integration(
            automation_id,
            'create_contact',
            parameters={'contact': contact_data}
        )
    
    async def update_contact(
        self,
        automation_id: str,
        contact_id: str,
        contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update contact in HubSpot"""
        return await self.execute_integration(
            automation_id,
            'update_contact',
            parameters={
                'contact_id': contact_id,
                'contact': contact_data
            }
        )
    
    async def get_contact(
        self,
        automation_id: str,
        contact_id: str
    ) -> Dict[str, Any]:
        """Get contact from HubSpot"""
        return await self.execute_integration(
            automation_id,
            'get_contact',
            parameters={'contact_id': contact_id}
        )
    
    async def delete_contact(
        self,
        automation_id: str,
        contact_id: str
    ) -> Dict[str, Any]:
        """Delete contact from HubSpot"""
        return await self.execute_integration(
            automation_id,
            'delete_contact',
            parameters={'contact_id': contact_id}
        )

class SalesforceIntegration(BaseIntegration):
    """Salesforce CRM Integration"""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str
    ):
        super().__init__("salesforce", {
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': password,
            'security_token': security_token
        })
    
    async def sync_leads(self, automation_id: str) -> Dict[str, Any]:
        """Sync leads from Salesforce"""
        return await self.execute_integration(automation_id, 'sync_leads')
    
    async def create_lead(
        self,
        automation_id: str,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create lead in Salesforce"""
        return await self.execute_integration(
            automation_id,
            'create_lead',
            parameters={'lead': lead_data}
        )
    
    async def update_lead(
        self,
        automation_id: str,
        lead_id: str,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update lead in Salesforce"""
        return await self.execute_integration(
            automation_id,
            'update_lead',
            parameters={
                'lead_id': lead_id,
                'lead': lead_data
            }
        )

# Base Integration Class
class BaseIntegration:
    """Base class for integrations"""
    
    def __init__(self, integration_type: str, config: Dict[str, Any]):
        self.type = integration_type
        self.config = config
        self.client = None  # Will be set when registered
    
    async def execute_integration(
        self,
        automation_id: str,
        action: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute integration action"""
        if not self.client:
            raise ValueError("Integration client not set")
        
        return await self.client.execute_integration(
            automation_id=automation_id,
            integration_type=self.type,
            action=action,
            parameters=parameters or {}
        )
```

## Ejemplos de Uso

```python
# sdk/python/examples/basic_usage.py
import asyncio
from windmill_platform import WindmillPlatformClient, AutomationConfig
from windmill_platform.integrations import HubSpotIntegration

async def main():
    # Initialize client
    async with WindmillPlatformClient(
        api_key="your-api-key",
        base_url="https://api.windmill-platform.io"
    ) as client:
        
        # Check platform status
        status = await client.get_status()
        print(f"Platform status: {status['status']}")
        
        # Create automation
        config = AutomationConfig(
            name="hubspot-contact-sync",
            description="Sync contacts from HubSpot every hour",
            template="crm-integration",
            schedule="0 * * * *",  # Every hour
            cpu="500m",
            memory="1Gi",
            environment_variables={
                "HUBSPOT_API_KEY": "${HUBSPOT_API_KEY}",
                "DATABASE_URL": "${DATABASE_URL}"
            },
            secrets=["hubspot-api-key", "database-credentials"]
        )
        
        automation = await client.create_automation(config)
        print(f"Created automation: {automation.id}")
        
        # Deploy automation
        deployment = await client.deploy_automation(
            automation_id=automation.id,
            environment="production",
            wait=True
        )
        print(f"Deployment status: {deployment.status}")
        
        # Execute manually
        execution = await client.execute_automation(
            automation_id=automation.id,
            parameters={"sync_type": "full"}
        )
        print(f"Execution started: {execution.execution_id}")
        
        # Wait for completion
        while True:
            status = await client.get_execution_status(execution.execution_id)
            if status.status in ["success", "failed", "timeout"]:
                break
            await asyncio.sleep(5)
        
        print(f"Execution completed: {status.status}")
        if status.status == "success":
            print(f"Output: {status.output}")
        else:
            print(f"Error: {status.error}")
        
        # Get usage metrics
        usage = await client.get_usage_metrics()
        print(f"Monthly executions: {usage.executions_count}")
        print(f"Success rate: {usage.success_rate:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# sdk/python/examples/integration_usage.py
import asyncio
from windmill_platform import WindmillPlatformClient, AutomationConfig
from windmill_platform.integrations import HubSpotIntegration

async def main():
    async with WindmillPlatformClient(
        api_key="your-api-key",
        base_url="https://api.windmill-platform.io"
    ) as client:
        
        # Create HubSpot integration
        hubspot = HubSpotIntegration(api_key="your-hubspot-api-key")
        
        # Create automation with HubSpot integration
        config = AutomationConfig(
            name="hubspot-lead-sync",
            description="Sync leads from HubSpot to database",
            template="webhook-processor",
            webhook="https://api.windmill-platform.io/webhooks/hubspot",
            environment_variables={
                "HUBSPOT_API_KEY": "${HUBSPOT_API_KEY}",
                "DATABASE_URL": "${DATABASE_URL}"
            }
        )
        
        automation = await client.create_automation(config)
        
        # Deploy and register integration
        await client.deploy_automation(automation.id)
        
        # Use integration methods
        contacts = await hubspot.sync_contacts(automation.id)
        print(f"Synced {len(contacts)} contacts")
        
        # Create new contact
        new_contact = await hubspot.create_contact(
            automation.id,
            {
                "email": "john@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "company": "Example Corp"
            }
        )
        print(f"Created contact: {new_contact['id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Instalación y Configuración

```bash
# Instalación del SDK
pip install windmill-platform-sdk

# Configuración de autenticación
export WINDMILL_API_KEY="your-api-key"
export WINDMILL_BASE_URL="https://api.windmill-platform.io"

# Uso básico
python -c "
from windmill_platform import SyncWindmillPlatformClient

with SyncWindmillPlatformClient() as client:
    status = client.get_status()
    print(f'Status: {status[\"status\"]}')
"
```

Este sistema SDK proporciona:

1. **Cliente asíncrono y síncrono** para diferentes casos de uso
2. **Gestión completa de automatizaciones** (CRUD, deployment, ejecución)
3. **Integraciones pre-construidas** con sistemas populares
4. **Manejo robusto de errores** y reintentos
5. **Modelos de datos type-safe** con Pydantic
6. **Soporte para webhooks y eventos**
7. **Monitoreo y métricas** integradas
8. **Gestión de secretos** y configuración
9. **Documentación inline** y ejemplos completos
10. **Multi-lenguaje** (Python, JavaScript, Go, Rust, Java)

El SDK está diseñado para ser intuitivo, robusto y escalable, permitiendo a los desarrolladores integrar Windmill Platform en sus aplicaciones con mínima fricción.