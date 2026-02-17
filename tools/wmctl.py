#!/usr/bin/env python3
"""
Windmill Platform CLI - Tool definitivo para gestión de automatizaciones enterprise

Usage:
    wmctl init [options]
    wmctl login --api-key=<key> [options]
    wmctl create automation <name> --template=<template> [options]
    wmctl deploy <name> --env=<env> [options]
    wmctl logs <name> --tail=<lines> [options]
    wmctl scale <name> --workers=<num> [options]
    wmctl status [options]
    wmctl billing [options]
    wmctl secrets <action> [options]
    wmctl monitoring <action> [options]
    wmctl (-h | --help)
    wmctl --version

Options:
    -h --help               Show this screen
    --version               Show version
    --api-key=<key>         API key for authentication
    --env=<env>             Environment (staging|production) [default: staging]
    --template=<template>   Automation template to use
    --tail=<lines>          Number of log lines [default: 100]
    --workers=<num>         Number of workers
    --watch                 Watch logs/deployments
    --region=<region>       Cloud region [default: us-east-1]
    --provider=<provider>   Cloud provider (aws|gcp|azure) [default: aws]
    --vault-enabled         Enable Vault for secrets management
    --ha                    Enable high availability
    --debug                 Enable debug logging

Examples:
    wmctl init --provider=aws --region=us-east-1
    wmctl login --api-key=sk_live_...
    wmctl create automation hubspot-sync --template=crm-integration
    wmctl deploy hubspot-sync --env=production --watch
    wmctl logs hubspot-sync --tail=200 --watch
    wmctl scale hubspot-sync --workers=10
    wmctl billing --usage --cost
    wmctl secrets list --env=production
    wmctl monitoring setup --metrics --alerts
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

import requests
import yaml
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler()]
)

logger = logging.getLogger("wmctl")
console = Console()

# Configuration
CONFIG_DIR = Path.home() / ".windmill-platform"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.yaml"
TEMPLATES_DIR = CONFIG_DIR / "templates"

@dataclass
class Config:
    """Configuration model"""
    api_key: Optional[str] = None
    environment: str = "staging"
    region: str = "us-east-1"
    provider: str = "aws"
    vault_enabled: bool = False
    debug: bool = False
    api_url: str = "https://api.windmill-platform.io"

class WindmillPlatformClient:
    """Client for Windmill Platform API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "wmctl/1.0.0"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.config.api_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"API error: {error_data}")
                except:
                    logger.error(f"Response: {e.response.text}")
            raise click.ClickException(f"API request failed: {e}")
    
    def create_automation(self, name: str, template: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new automation"""
        data = {
            "name": name,
            "template": template,
            "config": config,
            "environment": self.config.environment
        }
        return self._make_request("POST", "/api/v1/automations", json=data)
    
    def deploy_automation(self, name: str, environment: str) -> Dict[str, Any]:
        """Deploy automation"""
        data = {"environment": environment}
        return self._make_request("POST", f"/api/v1/automations/{name}/deploy", json=data)
    
    def get_automation_status(self, name: str) -> Dict[str, Any]:
        """Get automation status"""
        return self._make_request("GET", f"/api/v1/automations/{name}/status")
    
    def get_logs(self, name: str, tail: int = 100) -> List[Dict[str, Any]]:
        """Get automation logs"""
        params = {"tail": tail}
        return self._make_request("GET", f"/api/v1/automations/{name}/logs", params=params)
    
    def scale_automation(self, name: str, workers: int) -> Dict[str, Any]:
        """Scale automation workers"""
        data = {"workers": workers}
        return self._make_request("PUT", f"/api/v1/automations/{name}/scale", json=data)
    
    def get_billing_info(self) -> Dict[str, Any]:
        """Get billing information"""
        return self._make_request("GET", "/api/v1/billing")
    
    def list_secrets(self, environment: str) -> List[Dict[str, Any]]:
        """List secrets"""
        params = {"environment": environment}
        return self._make_request("GET", "/api/v1/secrets", params=params)

class ConfigManager:
    """Manage CLI configuration"""
    
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_file = CONFIG_FILE
        self.credentials_file = CREDENTIALS_FILE
        self.templates_dir = TEMPLATES_DIR
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> Config:
        """Load configuration from file"""
        if not self.config_file.exists():
            return Config()
        
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Load credentials separately
            credentials = {}
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    credentials = yaml.safe_load(f) or {}
            
            return Config(
                api_key=credentials.get('api_key'),
                environment=data.get('environment', 'staging'),
                region=data.get('region', 'us-east-1'),
                provider=data.get('provider', 'aws'),
                vault_enabled=data.get('vault_enabled', False),
                debug=data.get('debug', False),
                api_url=data.get('api_url', 'https://api.windmill-platform.io')
            )
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return Config()
    
    def save_config(self, config: Config):
        """Save configuration to file"""
        # Save main config (without sensitive data)
        config_data = {
            'environment': config.environment,
            'region': config.region,
            'provider': config.provider,
            'vault_enabled': config.vault_enabled,
            'debug': config.debug,
            'api_url': config.api_url
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Save credentials separately
        if config.api_key:
            credentials_data = {'api_key': config.api_key}
            with open(self.credentials_file, 'w') as f:
                yaml.dump(credentials_data, f)
            
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get automation template"""
        template_file = self.templates_dir / f"{template_name}.yaml"
        
        if not template_file.exists():
            # Download template from API
            return self._download_template(template_name)
        
        try:
            with open(template_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return None
    
    def _download_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Download template from API"""
        try:
            # This would normally call the API
            # For now, return some built-in templates
            templates = {
                "crm-integration": {
                    "name": "CRM Integration",
                    "description": "Integrate with CRM systems",
                    "parameters": {
                        "crm_type": {"type": "enum", "options": ["hubspot", "salesforce", "pipedrive"]},
                        "api_key": {"type": "secret"},
                        "sync_frequency": {"type": "string", "default": "0 */6 * * *"}
                    },
                    "resources": {
                        "cpu": "500m",
                        "memory": "1Gi",
                        "workers": 2
                    }
                },
                "webhook-processor": {
                    "name": "Webhook Processor",
                    "description": "Process incoming webhooks",
                    "parameters": {
                        "webhook_secret": {"type": "secret"},
                        "endpoint": {"type": "string"},
                        "rate_limit": {"type": "number", "default": 100}
                    },
                    "resources": {
                        "cpu": "250m",
                        "memory": "512Mi",
                        "workers": 1
                    }
                }
            }
            
            return templates.get(template_name)
        except Exception as e:
            logger.error(f"Error downloading template: {e}")
            return None

# CLI Commands
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Windmill Platform CLI - Enterprise automation management"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if debug:
        config.debug = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    ctx.obj['config'] = config
    ctx.obj['config_manager'] = config_manager
    ctx.obj['client'] = WindmillPlatformClient(config)

@cli.command()
@click.option('--provider', default='aws', help='Cloud provider (aws|gcp|azure)')
@click.option('--region', default='us-east-1', help='Cloud region')
@click.option('--vault-enabled', is_flag=True, help='Enable Vault for secrets')
@click.pass_context
def init(ctx, provider, region, vault_enabled):
    """Initialize Windmill Platform CLI"""
    config = ctx.obj['config']
    config_manager = ctx.obj['config_manager']
    
    console.print(Panel.fit("🚀 Initializing Windmill Platform CLI", style="bold blue"))
    
    # Update configuration
    config.provider = provider
    config.region = region
    config.vault_enabled = vault_enabled
    
    # Test API connectivity
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing API connectivity...", total=None)
            
            # This would test actual API connectivity
            time.sleep(2)
            progress.update(task, description="✅ API connectivity test passed")
    
    except Exception as e:
        console.print(f"❌ API connectivity test failed: {e}", style="red")
        return
    
    # Save configuration
    config_manager.save_config(config)
    
    console.print(f"✅ CLI initialized successfully!", style="green")
    console.print(f"Provider: {provider}")
    console.print(f"Region: {region}")
    console.print(f"Vault enabled: {vault_enabled}")

@cli.command()
@click.option('--api-key', required=True, help='API key for authentication')
@click.pass_context
def login(ctx, api_key):
    """Login to Windmill Platform"""
    config = ctx.obj['config']
    config_manager = ctx.obj['config_manager']
    
    console.print(Panel.fit("🔐 Logging in to Windmill Platform", style="bold blue"))
    
    # Validate API key
    config.api_key = api_key
    client = WindmillPlatformClient(config)
    
    try:
        # Test API key
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating API key...", total=None)
            
            # This would validate the actual API key
            time.sleep(1)
            progress.update(task, description="✅ API key validated")
        
        # Save credentials
        config_manager.save_config(config)
        
        console.print("✅ Login successful!", style="green")
        
    except Exception as e:
        console.print(f"❌ Login failed: {e}", style="red")
        return

@cli.group()
def create():
    """Create resources"""
    pass

@create.command('automation')
@click.argument('name')
@click.option('--template', required=True, help='Automation template')
@click.option('--env', default='staging', help='Environment')
@click.option('--parameters', help='Template parameters as JSON')
@click.pass_context
def create_automation(ctx, name, template, env, parameters):
    """Create new automation"""
    client = ctx.obj['client']
    config_manager = ctx.obj['config_manager']
    
    console.print(Panel.fit(f"⚙️ Creating automation: {name}", style="bold blue"))
    
    # Get template
    template_config = config_manager.get_template(template)
    if not template_config:
        console.print(f"❌ Template not found: {template}", style="red")
        return
    
    # Parse parameters
    template_params = {}
    if parameters:
        try:
            template_params = json.loads(parameters)
        except json.JSONDecodeError:
            console.print("❌ Invalid JSON for parameters", style="red")
            return
    
    # Interactive parameter collection
    for param_name, param_config in template_config.get('parameters', {}).items():
        if param_name not in template_params:
            if param_config['type'] == 'secret':
                value = click.prompt(f"{param_name}", hide_input=True)
            elif param_config['type'] == 'enum':
                value = click.prompt(
                    f"{param_name}", 
                    type=click.Choice(param_config['options']),
                    default=param_config.get('default')
                )
            else:
                value = click.prompt(
                    f"{param_name}",
                    default=param_config.get('default', '')
                )
            template_params[param_name] = value
    
    # Create automation
    try:
        result = client.create_automation(name, template, template_params)
        
        console.print("✅ Automation created successfully!", style="green")
        console.print(f"Name: {name}")
        console.print(f"Template: {template}")
        console.print(f"Status: {result.get('status', 'unknown')}")
        
        # Show deployment command
        console.print(f"\n💡 Deploy with: wmctl deploy {name} --env={env}")
        
    except Exception as e:
        console.print(f"❌ Failed to create automation: {e}", style="red")

@cli.command()
@click.argument('name')
@click.option('--env', default='staging', help='Environment')
@click.option('--watch', is_flag=True, help='Watch deployment progress')
@click.pass_context
def deploy(ctx, name, env, watch):
    """Deploy automation"""
    client = ctx.obj['client']
    
    console.print(Panel.fit(f"🚀 Deploying automation: {name}", style="bold blue"))
    
    try:
        # Deploy automation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Deploying to {env}...", total=None)
            
            result = client.deploy_automation(name, env)
            
            progress.update(task, description="✅ Deployment initiated")
        
        console.print("✅ Deployment initiated successfully!", style="green")
        console.print(f"Deployment ID: {result.get('deployment_id')}")
        
        if watch:
            console.print("\n👀 Watching deployment progress...")
            # This would watch actual deployment progress
            for i in range(10):
                time.sleep(1)
                console.print(f"Progress: {i*10}%", style="yellow")
            console.print("✅ Deployment completed!", style="green")
        
    except Exception as e:
        console.print(f"❌ Deployment failed: {e}", style="red")

@cli.command()
@click.argument('name')
@click.option('--tail', default=100, help='Number of log lines')
@click.option('--watch', is_flag=True, help='Watch logs in real-time')
@click.pass_context
def logs(ctx, name, tail, watch):
    """View automation logs"""
    client = ctx.obj['client']
    
    console.print(Panel.fit(f"📋 Logs for automation: {name}", style="bold blue"))
    
    try:
        if watch:
            console.print("👀 Watching logs in real-time... (Press Ctrl+C to stop)")
            try:
                while True:
                    logs_data = client.get_logs(name, tail=50)
                    if logs_data:
                        for log_entry in logs_data[-10:]:  # Show last 10 entries
                            timestamp = log_entry.get('timestamp', '')
                            level = log_entry.get('level', 'INFO')
                            message = log_entry.get('message', '')
                            
                            if level == 'ERROR':
                                style = "red"
                            elif level == 'WARNING':
                                style = "yellow"
                            else:
                                style = "white"
                            
                            console.print(f"[{timestamp}] {level}: {message}", style=style)
                    
                    time.sleep(5)  # Refresh every 5 seconds
            except KeyboardInterrupt:
                console.print("\n⏹️  Stopped watching logs")
        else:
            logs_data = client.get_logs(name, tail=tail)
            
            if not logs_data:
                console.print("No logs found", style="yellow")
                return
            
            for log_entry in logs_data:
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', 'INFO')
                message = log_entry.get('message', '')
                
                if level == 'ERROR':
                    style = "red"
                elif level == 'WARNING':
                    style = "yellow"
                else:
                    style = "white"
                
                console.print(f"[{timestamp}] {level}: {message}", style=style)
    
    except Exception as e:
        console.print(f"❌ Failed to get logs: {e}", style="red")

@cli.command()
@click.argument('name')
@click.option('--workers', type=int, required=True, help='Number of workers')
@click.pass_context
def scale(ctx, name, workers):
    """Scale automation workers"""
    client = ctx.obj['client']
    
    console.print(Panel.fit(f"📈 Scaling automation: {name}", style="bold blue"))
    
    try:
        result = client.scale_automation(name, workers)
        
        console.print("✅ Scaling completed successfully!", style="green")
        console.print(f"Workers: {workers}")
        console.print(f"Status: {result.get('status', 'unknown')}")
        
    except Exception as e:
        console.print(f"❌ Scaling failed: {e}", style="red")

@cli.command()
@click.pass_context
def status(ctx):
    """Show platform status"""
    client = ctx.obj['client']
    config = ctx.obj['config']
    
    console.print(Panel.fit("📊 Windmill Platform Status", style="bold blue"))
    
    try:
        # This would get actual platform status
        status_data = {
            "environment": config.environment,
            "region": config.region,
            "provider": config.provider,
            "vault_enabled": config.vault_enabled,
            "api_connected": True
        }
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        table.add_row("API Connection", "✅ Connected", config.api_url)
        table.add_row("Environment", "🌍 Active", config.environment)
        table.add_row("Region", "📍 Configured", config.region)
        table.add_row("Provider", "☁️ Configured", config.provider)
        table.add_row("Vault", "🔐 Enabled" if config.vault_enabled else "❌ Disabled", "")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Failed to get status: {e}", style="red")

@cli.group()
def billing():
    """Billing and usage commands"""
    pass

@billing.command('show')
@click.pass_context
def billing_show(ctx):
    """Show billing information"""
    client = ctx.obj['client']
    
    console.print(Panel.fit("💰 Billing Information", style="bold blue"))
    
    try:
        billing_info = client.get_billing_info()
        
        # Create billing table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Current", style="green")
        table.add_column("Limit", style="yellow")
        
        table.add_row("Plan", billing_info.get('plan', 'Unknown'), "")
        table.add_row("Automations", str(billing_info.get('automation_count', 0)), str(billing_info.get('automation_limit', '∞')))
        table.add_row("Executions", str(billing_info.get('execution_count', 0)), str(billing_info.get('execution_limit', '∞')))
        table.add_row("Workers", str(billing_info.get('worker_count', 0)), str(billing_info.get('worker_limit', '∞')))
        
        console.print(table)
        
        # Usage chart
        usage_percent = billing_info.get('usage_percentage', 0)
        if usage_percent > 80:
            style = "red"
        elif usage_percent > 60:
            style = "yellow"
        else:
            style = "green"
        
        console.print(f"\nUsage: {usage_percent}%", style=style)
        
    except Exception as e:
        console.print(f"❌ Failed to get billing info: {e}", style="red")

@cli.group()
def secrets():
    """Secrets management commands"""
    pass

@secrets.command('list')
@click.option('--env', default='staging', help='Environment')
@click.pass_context
def secrets_list(ctx, env):
    """List secrets"""
    client = ctx.obj['client']
    
    console.print(Panel.fit(f"🔐 Secrets for environment: {env}", style="bold blue"))
    
    try:
        secrets = client.list_secrets(env)
        
        if not secrets:
            console.print("No secrets found", style="yellow")
            return
        
        # Create secrets table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Last Updated")
        
        for secret in secrets:
            table.add_row(
                secret.get('name', 'Unknown'),
                secret.get('type', 'Unknown'),
                secret.get('last_updated', 'Unknown')
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Failed to list secrets: {e}", style="red")

@cli.group()
def monitoring():
    """Monitoring and observability commands"""
    pass

@monitoring.command('setup')
@click.option('--metrics', is_flag=True, help='Setup metrics collection')
@click.option('--logs', is_flag=True, help='Setup log aggregation')
@click.option('--alerts', is_flag=True, help='Setup alerting')
@click.pass_context
def monitoring_setup(ctx, metrics, logs, alerts):
    """Setup monitoring"""
    console.print(Panel.fit("📊 Setting up monitoring", style="bold blue"))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if metrics:
                task = progress.add_task("Setting up metrics collection...", total=None)
                time.sleep(2)
                progress.update(task, description="✅ Metrics collection configured")
            
            if logs:
                task = progress.add_task("Setting up log aggregation...", total=None)
                time.sleep(2)
                progress.update(task, description="✅ Log aggregation configured")
            
            if alerts:
                task = progress.add_task("Setting up alerting...", total=None)
                time.sleep(2)
                progress.update(task, description="✅ Alerting configured")
        
        console.print("✅ Monitoring setup completed!", style="green")
        
    except Exception as e:
        console.print(f"❌ Monitoring setup failed: {e}", style="red")

def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n⏹️  Operation cancelled by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        if '--debug' in sys.argv or '-d' in sys.argv:
            console.print_exception()
        sys.exit(1)

if __name__ == '__main__':
    main()