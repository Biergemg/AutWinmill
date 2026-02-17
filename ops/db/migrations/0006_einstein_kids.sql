-- Einstein Kids Database Schema
-- Tablas específicas para el proyecto de Cyn

-- 1. Tabla de leads (clientes potenciales)
CREATE TABLE IF NOT EXISTS ek_leads (
    lead_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avatar VARCHAR(20) CHECK (avatar IN ('mother', 'therapist')),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    phone_normalized VARCHAR(20) UNIQUE,
    email_normalized VARCHAR(255) UNIQUE,
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

CREATE INDEX idx_ek_leads_phone_normalized ON ek_leads(phone_normalized);
CREATE INDEX idx_ek_leads_email_normalized ON ek_leads(email_normalized);
CREATE INDEX idx_ek_leads_stage ON ek_leads(stage);
CREATE INDEX idx_ek_leads_score ON ek_leads(score) WHERE score >= 70;

-- 2. Tabla de trabajos programados (scheduler persistente)
CREATE TABLE IF NOT EXISTS ek_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    run_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'cancelled', 'failed')),
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_jobs_scheduled ON ek_jobs(status, run_at) WHERE status = 'scheduled';
CREATE INDEX idx_ek_jobs_lead_id ON ek_jobs(lead_id);

-- 3. Tabla de eventos (event sourcing)
CREATE TABLE IF NOT EXISTS ek_lead_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    ts TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_lead_events_lead_id ON ek_lead_events(lead_id);
CREATE INDEX idx_ek_lead_events_type ON ek_lead_events(event_type);

-- 4. Tabla de mensajes WhatsApp
CREATE TABLE IF NOT EXISTS ek_ycloud_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ycloud_message_id VARCHAR(100) UNIQUE,
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    direction VARCHAR(20) CHECK (direction IN ('inbound', 'outbound')),
    message_type VARCHAR(20) CHECK (message_type IN ('text', 'template', 'interactive', 'media')),
    template_key VARCHAR(100),
    template_name VARCHAR(100),
    content JSONB NOT NULL,
    status VARCHAR(20) CHECK (status IN ('accepted', 'sent', 'delivered', 'read', 'failed')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_ycloud_messages_lead_id ON ek_ycloud_messages(lead_id);
CREATE INDEX idx_ek_ycloud_messages_status ON ek_ycloud_messages(status);
CREATE INDEX idx_ek_ycloud_messages_yc_id ON ek_ycloud_messages(ycloud_message_id);

-- 5. Tabla de ventas/pagos
CREATE TABLE IF NOT EXISTS ek_sales (
    sale_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    provider VARCHAR(50) DEFAULT 'vitalhealth',
    status VARCHAR(20) CHECK (status IN ('claimed', 'confirmed', 'rejected')),
    amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'MXN',
    external_ref VARCHAR(255),
    proof JSONB,
    confirmed_by VARCHAR(50),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_sales_lead_id ON ek_sales(lead_id);
CREATE INDEX idx_ek_sales_status ON ek_sales(status);

-- 6. Tabla de partners (terapeutas)
CREATE TABLE IF NOT EXISTS ek_partners (
    partner_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('applied', 'approved', 'active', 'rejected')),
    specialty VARCHAR(100),
    city VARCHAR(100),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_partners_lead_id ON ek_partners(lead_id);
CREATE INDEX idx_ek_partners_status ON ek_partners(status);

-- 7. Tabla de grupos WhatsApp
CREATE TABLE IF NOT EXISTS ek_groups (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id VARCHAR(100) UNIQUE NOT NULL,
    group_type VARCHAR(50) NOT NULL,
    group_link TEXT NOT NULL,
    capacity INTEGER DEFAULT 256,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ek_groups_cohort ON ek_groups(cohort_id);
CREATE INDEX idx_ek_groups_active ON ek_groups(is_active);

-- 8. Tabla de membresías a grupos
CREATE TABLE IF NOT EXISTS ek_group_memberships (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES ek_leads(lead_id) ON DELETE CASCADE,
    group_id UUID REFERENCES ek_groups(group_id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('invited', 'joined', 'left')),
    joined_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lead_id, group_id)
);

CREATE INDEX idx_ek_group_memberships_lead ON ek_group_memberships(lead_id);
CREATE INDEX idx_ek_group_memberships_group ON ek_group_memberships(group_id);

-- Función para actualizar timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER trg_ek_leads_updated_at BEFORE UPDATE ON ek_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ek_jobs_updated_at BEFORE UPDATE ON ek_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ek_sales_updated_at BEFORE UPDATE ON ek_sales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ek_partners_updated_at BEFORE UPDATE ON ek_partners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ek_groups_updated_at BEFORE UPDATE ON ek_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_ek_group_memberships_updated_at BEFORE UPDATE ON ek_group_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();