# Software Requirements Specification (IEEE 830)

## 1. Introducción
- Propósito: Automatizaciones Windmill con validación, orquestación y auditoría.
- Alcance: Ingesta de eventos, validación por contratos, DLQ, métricas y RBAC.

## 2. Descripción general
- Usuarios: Admins, Developers, Operators, Auditors.
- Suposiciones: Postgres 15, Windmill operativo, CI/CD GitHub Actions.

## 3. Requisitos funcionales
- Validación de payloads contra contratos (jsonschema/pydantic).
- Orquestación de flujos con reintentos y DLQ.
- Auditoría de acciones de plataforma y métricas.

## 4. Requisitos no funcionales
- Cobertura ≥80%, maintainability rating A.
- Latencia p95 validación con +50% mejora.
- Seguridad PII masking y RBAC hardening.

## 5. Restricciones
- Dependencia en contenedor Postgres y Windmill.
- Migraciones reversibles y gates de calidad bloqueantes.

## 6. Aceptación
- E2E MVP pasa y SonarQube gate activo (M4+).
