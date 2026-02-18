# Plan de Capacidad y Pruebas de Performance

## Objetivo
Establecer una suite de pruebas reproducible para validar la escalabilidad, aislamiento multi-tenant y estabilidad del sistema AutWinmill bajo cargas de trabajo simuladas y condiciones adversas.

## Escenarios de Prueba

### 1. Load Testing (Carga Normal y Pico)
- **Objetivo**: Determinar el comportamiento del sistema bajo carga esperada y picos predecibles.
- **Herramienta**: Locust.
- **Escenarios**:
    - **Baseline**: 1 usuario/worker (verificar funcionalidad base y latencia mínima).
    - **Normal**: 10 usuarios concurrentes.
    - **High**: 50 usuarios concurrentes.
    - **Burst**: 100 usuarios concurrentes (pico corto).
- **Métricas**: RPS (Requests per Second), Latencia (p50, p95, p99), Tasa de Error.
- **Criterio de Éxito**: Latencia p95 < 2s, Error Rate < 1%.

### 2. Stress Testing (Punto de Quiebre)
- **Objetivo**: Encontrar el límite de ruptura del sistema.
- **Estrategia**: Ramp-up progresivo de usuarios hasta que el fallo sea > 20% o latencia > 10s.
- **Métricas**: Max Concurrent Users, Resource Usage (CPU/RAM si disponible).

### 3. Soak Testing (Resistencia)
- **Objetivo**: Detectar fugas de memoria o degradación de rendimiento en el tiempo.
- **Escenario**: Carga constante (e.g., 20 usuarios) durante un periodo extendido (diseño para 1h+, prueba corta de 5-10m).

### 4. Pruebas Multi-tenant
- **Objetivo**: Verificar que los datos y la ejecución de un tenant no interfieran con otro.
- **Estrategia**:
    - Ejecutar N workers concurrentes con diferentes `WM_WORKSPACE` o identificadores de tenant.
    - Validar que las respuestas contengan solo datos del tenant solicitante.
    - Validar que el rendimiento no se degrade desproporcionadamente con más tenants (ruido de vecinos).

### 5. Resilience & Chaos Testing
- **Objetivo**: Validar recuperación ante fallos.
- **Escenarios**:
    - **Database Outage**: Simular pérdida de conexión a DB (mock o real si dockerizado).
    - **External API Latency**: Simular lentitud en APIs de terceros.
    - **Webhooks Duplicados**: Enviar el mismo payload dos veces y verificar idempotencia.

### 6. Security Smoke Tests
- **Objetivo**: Validación rápida de posturas de seguridad.
- **Escenarios**:
    - Intento de ejecución sin token/credenciales.
    - Intento de acceso a recursos de otro tenant (simulado).
    - Verificación de logs para asegurar que no hay secretos expuestos.

## Automatización y Reporte
- **Ejecución**: Scripts en `scripts/benchmark.sh` y Makefile.
- **CI/CD**: Workflow de GitHub Actions (`performance.yml`) con ejecución manual (`workflow_dispatch`).
- **Reportes**: Salida en consola y archivos JSON/Markdown en `ops/benchmarks/results/`.
