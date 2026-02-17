-- Script de migración simplificado para Einstein Kids
-- Ejecutar este script en PostgreSQL

-- 1. Crear tabla de leads
CREATE TABLE IF NOT EXISTS ek_leads (
    lead_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar VARCHAR(20) CHECK (avatar IN ('mother', 'therapist')),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    phone_normalized VARCHAR(20),
    utm_source VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_content VARCHAR(100),
    utm_medium VARCHAR(100),
    landing_id VARCHAR(100),
    event_start_at TIMESTAMP WITH TIME ZONE,
    stage VARCHAR(50) DEFAULT 'NEW_LEAD',
    score INTEGER DEFAULT 0,
    whatsapp_consent_ts TIMESTAMP WITH TIME ZONE,
    email_consent_ts TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices básicos
CREATE INDEX IF NOT EXISTS idx_ek_leads_phone ON ek_leads(phone_normalized);
CREATE INDEX IF NOT EXISTS idx_ek_leads_stage ON ek_leads(stage);

-- 2. Crear tabla de trabajos
CREATE TABLE IF NOT EXISTS ek_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id),
    job_type VARCHAR(50) NOT NULL,
    run_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ek_jobs_scheduled ON ek_jobs(status, run_at);

-- 3. Crear tabla de eventos
CREATE TABLE IF NOT EXISTS ek_lead_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Crear tabla de mensajes
CREATE TABLE IF NOT EXISTS ek_ycloud_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id),
    direction VARCHAR(20),
    message_type VARCHAR(20),
    template_key VARCHAR(100),
    content JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'accepted',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Crear tabla de ventas
CREATE TABLE IF NOT EXISTS ek_sales (
    sale_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id),
    provider VARCHAR(50) DEFAULT 'vitalhealth',
    status VARCHAR(20) DEFAULT 'claimed',
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'MXN',
    external_ref VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insertar datos de prueba
INSERT INTO ek_leads (name, email, phone, phone_normalized, avatar, stage, score) VALUES 
('María García', 'maria@test.com', '55 1234 5678', '+525512345678', 'mother', 'NEW_LEAD', 0),
('Ana López', 'ana@test.com', '55 8765 4321', '+525587654321', 'mother', 'NEW_LEAD', 0)
ON CONFLICT DO NOTHING;

SELECT '✅ Tablas Einstein Kids creadas exitosamente' as status;