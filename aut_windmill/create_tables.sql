-- Einstein Kids - Tablas básicas
-- Ejecutar con: docker exec -i aut_windmill_postgres psql -U windmill -d windmill < create_tables.sql

-- Tabla principal de leads
CREATE TABLE ek_leads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    avatar VARCHAR(20) DEFAULT 'mother',
    stage VARCHAR(50) DEFAULT 'NEW_LEAD',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de trabajos programados
CREATE TABLE ek_jobs (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES ek_leads(id),
    job_type VARCHAR(50) NOT NULL,
    run_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de mensajes
CREATE TABLE ek_messages (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES ek_leads(id),
    direction VARCHAR(20) DEFAULT 'outbound',
    content TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insertar datos de prueba
INSERT INTO ek_leads (name, phone, email, avatar, stage) VALUES 
('María García', '5512345678', 'maria@test.com', 'mother', 'NEW_LEAD'),
('Ana López', '5587654321', 'ana@test.com', 'mother', 'NEW_LEAD');

-- Verificar que se crearon
SELECT 'Tablas creadas y datos insertados' as resultado;
SELECT * FROM ek_leads;