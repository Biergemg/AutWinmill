#!/usr/bin/env python3
"""
Dashboard de Alto Calibre - Einstein Kids
Panel principal donde Cyn puede ver TODO su negocio
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class EinsteinKidsDashboard:
    """Dashboard completo para Cyn"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
    
    def get_resumen_general(self) -> Dict[str, Any]:
        """Resumen general del negocio"""
        cursor = self.conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM ek_leads;")
        total_leads = cursor.fetchone()[0]
        
        # Leads por avatar
        cursor.execute("""
            SELECT avatar, COUNT(*) as count 
            FROM ek_leads 
            GROUP BY avatar;
        """)
        leads_por_avatar = dict(cursor.fetchall())
        
        # Leads por etapa
        cursor.execute("""
            SELECT stage, COUNT(*) as count 
            FROM ek_leads 
            GROUP BY stage 
            ORDER BY count DESC;
        """)
        leads_por_etapa = dict(cursor.fetchall())
        
        # Ventas confirmadas
        cursor.execute("SELECT COUNT(*) FROM ek_sales WHERE status = 'confirmed';")
        ventas_confirmadas = cursor.fetchone()[0]
        
        # Monto total
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM ek_sales WHERE status = 'confirmed';")
        monto_total = float(cursor.fetchone()[0] or 0)
        
        return {
            "resumen": {
                "total_leads": total_leads,
                "ventas_confirmadas": ventas_confirmadas,
                "monto_total": monto_total,
                "conversion_rate": round((ventas_confirmadas / max(total_leads, 1)) * 100, 2)
            },
            "leads_por_avatar": leads_por_avatar,
            "leads_por_etapa": leads_por_etapa
        }
    
    def get_proximo_evento(self) -> Dict[str, Any]:
        """Pr??ximo evento/masterclass"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                MIN(event_start_at) as proximo_evento,
                COUNT(*) as inscritos
            FROM ek_leads 
            WHERE event_start_at > NOW()
            GROUP BY DATE(event_start_at)
            ORDER BY proximo_evento
            LIMIT 1;
        """)
        
        result = cursor.fetchone()
        if result:
            return {
                "fecha": result[0].strftime("%Y-%m-%d %H:%M"),
                "inscritos": result[1],
                "dias_restantes": (result[0] - datetime.now()).days
            }
        return None
    
    def get_leads_calientes(self) -> List[Dict[str, Any]]:
        """Leads con alta puntuaci??n (hot leads)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                lead_id, name, phone, email, score, stage,
                whatsapp_consent_ts, created_at
            FROM ek_leads 
            WHERE score >= 70 
            ORDER BY score DESC, created_at DESC
            LIMIT 10;
        """)
        
        leads = []
        for row in cursor.fetchall():
            leads.append({
                "id": str(row[0]),
                "nombre": row[1],
                "telefono": row[2],
                "email": row[3],
                "score": row[4],
                "etapa": row[5],
                "consentimiento": row[6].strftime("%Y-%m-%d") if row[6] else None,
                "fecha_registro": row[7].strftime("%Y-%m-%d %H:%M")
            })
        
        return leads
    
    def get_claims_pendientes(self) -> List[Dict[str, Any]]:
        """Claims de pago pendientes de revisi??n"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                s.sale_id, s.lead_id, l.name, l.phone, 
                s.created_at, s.proof
            FROM ek_sales s
            JOIN ek_leads l ON s.lead_id = l.lead_id
            WHERE s.status = 'claimed'
            ORDER BY s.created_at DESC;
        """)
        
        claims = []
        for row in cursor.fetchall():
            claims.append({
                "claim_id": str(row[0]),
                "lead_id": str(row[1]),
                "nombre": row[2],
                "telefono": row[3],
                "fecha_claim": row[4].strftime("%Y-%m-%d %H:%M"),
                "proof": row[5]
            })
        
        return claims
    
    def get_mensajes_recientes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Mensajes WhatsApp recientes"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.id, m.direction, m.message_type, m.status,
                l.name, m.created_at
            FROM ek_ycloud_messages m
            JOIN ek_leads l ON m.lead_id = l.lead_id
            ORDER BY m.created_at DESC
            LIMIT %s;
        """, (limit,))
        
        mensajes = []
        for row in cursor.fetchall():
            mensajes.append({
                "id": str(row[0]),
                "direccion": row[1],
                "tipo": row[2],
                "estado": row[3],
                "nombre": row[4],
                "fecha": row[5].strftime("%Y-%m-%d %H:%M")
            })
        
        return mensajes
    
    def get_eventos_proximos(self, dias: int = 7) -> List[Dict[str, Any]]:
        """Eventos pr??ximos con asistencia"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(event_start_at) as fecha,
                COUNT(*) as inscritos,
                COUNT(CASE WHEN stage = 'EVENT_ATTENDED' THEN 1 END) as asistieron,
                COUNT(CASE WHEN stage = 'EVENT_NO_SHOW' THEN 1 END) as no_show
            FROM ek_leads 
            WHERE event_start_at BETWEEN NOW() AND NOW() + INTERVAL '%s days'
            GROUP BY DATE(event_start_at)
            ORDER BY fecha;
        """, (dias,))
        
        eventos = []
        for row in cursor.fetchall():
            fecha = row[0]
            inscritos = row[1]
            asistieron = row[2]
            no_show = row[3]
            
            eventos.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "inscritos": inscritos,
                "asistieron": asistieron,
                "no_show": no_show,
                "tasa_asistencia": round((asistieron / max(inscritos, 1)) * 100, 1)
            })
        
        return eventos
    
    def get_kpis_diarios(self, dias: int = 30) -> Dict[str, Any]:
        """KPIs diarios para dashboard"""
        cursor = self.conn.cursor()
        
        # Leads nuevos por d??a
        cursor.execute("""
            SELECT 
                DATE(created_at) as fecha,
                COUNT(*) as leads_nuevos
            FROM ek_leads 
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY fecha DESC;
        """, (dias,))
        
        leads_diarios = []
        for row in cursor.fetchall():
            leads_diarios.append({
                "fecha": row[0].strftime("%Y-%m-%d"),
                "leads": row[1]
            })
        
        # Ventas por d??a
        cursor.execute("""
            SELECT 
                DATE(confirmed_at) as fecha,
                COUNT(*) as ventas,
                COALESCE(SUM(amount), 0) as monto
            FROM ek_sales 
            WHERE status = 'confirmed' 
            AND confirmed_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(confirmed_at)
            ORDER BY fecha DESC;
        """, (dias,))
        
        ventas_diarias = []
        for row in cursor.fetchall():
            ventas_diarias.append({
                "fecha": row[0].strftime("%Y-%m-%d"),
                "ventas": row[1],
                "monto": float(row[2])
            })
        
        return {
            "leads_diarios": leads_diarios,
            "ventas_diarias": ventas_diarias,
            "periodo_dias": dias
        }
    
    def generar_reporte_completo(self) -> Dict[str, Any]:
        """Genera reporte completo para Cyn"""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resumen_general": self.get_resumen_general(),
            "proximo_evento": self.get_proximo_evento(),
            "leads_calientes": self.get_leads_calientes(),
            "claims_pendientes": self.get_claims_pendientes(),
            "mensajes_recientes": self.get_mensajes_recientes(),
            "eventos_proximos": self.get_eventos_proximos(),
            "kpis_diarios": self.get_kpis_diarios()
        }
    
    def close(self):
        """Cierra conexi??n a BD"""
        if self.conn:
            self.conn.close()

# Funci??n principal para Windmill
if __name__ == "__main__":
    dashboard = EinsteinKidsDashboard()
    try:
        reporte = dashboard.generar_reporte_completo()
        print(json.dumps(reporte, indent=2, ensure_ascii=False))
    finally:
        dashboard.close()
