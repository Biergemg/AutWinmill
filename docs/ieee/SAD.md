# Software Architecture Description (IEEE 1471/42010)

## Arquitectura Hexagonal
- Dominio: Validadores y orquestadores.
- Puertos: EventIngress, Persistence, Metrics.
- Adaptadores: Windmill, Postgres (Docker), Docker CLI.

## Patrones
- Strategy, Repository, Adapter, Circuit Breaker/Retry, Outbox+DLQ.

## Vistas
- Lógica: validación Strategy → orquestación.
- Implementación: src/windmill_automation/*, scripts/core/*, ops/db/*.

## Decisiones
- jsonschema con fallback interno.
- Repository sobre adapter Docker sin credenciales directas.

## Calidad
- Observabilidad JSON + OTel cuando esté disponible.
- Gates SonarQube (coverage, duplicación, smells, vulnerabilidades).
