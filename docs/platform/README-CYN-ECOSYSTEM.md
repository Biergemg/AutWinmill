# Ecosistema Cyn - Einstein Kids

Este directorio contiene TODO el ecosistema de Cyn para Einstein Kids, limpio y optimizado.

## 📁 Estructura del Proyecto

```
aut_windmill/
├── f/einstein_kids/              # Scripts y lógica de negocio
│   ├── dashboard/                # Dashboards de Cyn
│   ├── knowledge_base/           # Base de conocimiento
│   ├── moms/                     # Secuencias para mamás
│   ├── shared/                   # Scripts compartidos
│   └── therapists/               # Secuencias para terapeutas
├── flows/                        # Flujos de automatización
├── ops/                          # Configuración Docker
└── resources/                    # Configuraciones
```

## 🎯 Componentes Principales

### 🤖 Agente AI de Cyn
- **Archivo**: `f/einstein_kids/shared/ai_agent_cyn.py`
- **Función**: Personalidad completa de Cyn con detección de intenciones
- **Integraciones**: Clawbot.ai, WhatsApp, Zoom, Calendly

### 📚 Base de Conocimiento
- **Archivo**: `f/einstein_kids/knowledge_base/cyn_knowledge.yaml`
- **Contenido**: Toda la información de clases, respuestas, técnicas por edad

### 🔄 Flujos de Automatización
- **Masterclass**: Booking → Pre-evento → Asistencia → Cierre
- **AI Agent**: Respuestas automáticas con escalación humana
- **Integraciones**: Zoom, Calendly, WhatsApp

### 📊 Dashboard
- **Archivo**: `f/einstein_kids/dashboard/ai_dashboard.html`
- **Función**: Monitoreo en tiempo real de leads y eventos

## 🚀 Inicio Rápido

```bash
# Entrar al directorio
cd aut_windmill/ops

# Configurar variables de entorno
cp .env.cyn.example .env
# Editar .env con tus credenciales

# Iniciar ecosistema
./start-cyn-ecosystem.sh
```

## 🔧 Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Windmill | 8001 | Automatizaciones |
| PostgreSQL | 5433 | Base de datos |
| Redis | 6380 | Caché |
| Prometheus | 9091 | Monitoreo |

## 📋 Flujos Implementados

### 1. Masterclass 2025
```
Traffic → Calendly Booking → Pre-evento (A.I.M.) → Zoom Live → Cierre
```

### 2. AI Agent
```
Mensaje → Preprocessing → Intent Detection → Cyn Response → Human Escalation
```

### 3. Show-up Maximization
- Acknowledge: Reconocer booking inmediatamente
- Include: Hacer sentir parte de la comunidad  
- Mobilize: Recordatorios estratégicos

## 🔐 Seguridad

- **Clawbot Guardrails**: No medical advice, no high-pressure sales
- **Webhook Validation**: HMAC signatures para Zoom y Calendly
- **Data Encryption**: En tránsito y en reposo
- **Rate Limiting**: Protección contra spam

## 📈 Métricas Clave

- **Show-up Rate**: Target 60-70%
- **Lead Score**: 0-100 (≥80 va a humanos)
- **Response Time**: <2 minutos para AI
- **Conversion Rate**: Tracking completo del funnel

## 🆘 Soporte

### Archivos de Auditoría
- `f/einstein_kids/shared/system_audit.py`
- Valida conectividad de todos los componentes

### Troubleshooting
```bash
# Ver logs
docker-compose -f docker-compose-cyn.yml logs -f

# Reiniciar servicio
docker-compose -f docker-compose-cyn.yml restart windmill-cyn

# Estado de servicios
docker-compose -f docker-compose-cyn.yml ps
```

## 📞 Contacto

Para soporte técnico o configuración:
- Revisar `ops/README-CYN.md` Verificar logs en tiempo real
- Usar script de auditoría para diagnóstico

---

**✅ Ecosistema Cyn completamente funcional y optimizado!**