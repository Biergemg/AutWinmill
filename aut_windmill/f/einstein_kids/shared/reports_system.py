"""
Sistema de Reportes y Conversiones para Einstein Kids
Genera reportes diarios, KPIs y m??tricas de conversi??n
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class EinsteinKidsReports:
    """Sistema completo de reportes para Cyn"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Genera reporte diario completo"""
        if date is None:
            date = datetime.now().date()
        
        cursor = self.conn.cursor()
        
        # Leads nuevos del d??a
        cursor.execute("""
            SELECT 
                COUNT(*) as leads_nuevos,
                COUNT(CASE WHEN avatar = 'mother' THEN 1 END) as moms,
                COUNT(CASE WHEN avatar = 'therapist' THEN 1 END) as therapists
            FROM ek_leads 
            WHERE DATE(created_at) = %s;
        """, (date,))
        
        leads_data = cursor.fetchone()
        
        # Mensajes enviados
        cursor.execute("""
            SELECT 
                COUNT(*) as total_mensajes,
                COUNT(CASE WHEN direction = 'outbound' THEN 1 END) as enviados,
                COUNT(CASE WHEN direction = 'inbound' THEN 1 END) as recibidos,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as entregados,
                COUNT(CASE WHEN status = 'read' THEN 1 END) as leidos
            FROM ek_ycloud_messages 
            WHERE DATE(created_at) = %s;
        """, (date,))
        
        mensajes_data = cursor.fetchone()
        
        # Ventas del d??a
        cursor.execute("""
            SELECT 
                COUNT(*) as ventas,
                COALESCE(SUM(amount), 0) as monto_total,
                AVG(amount) as promedio_venta
            FROM ek_sales 
            WHERE DATE(confirmed_at) = %s 
            AND status = 'confirmed';
        """, (date,))
        
        ventas_data = cursor.fetchone()
        
        # Eventos del d??a
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT DATE(event_start_at)) as eventos,
                COUNT(CASE WHEN stage = 'EVENT_ATTENDED' THEN 1 END) as asistieron,
                COUNT(CASE WHEN stage = 'EVENT_NO_SHOW' THEN 1 END) as no_show
            FROM ek_leads 
            WHERE DATE(event_start_at) = %s;
        """, (date,))
        
        eventos_data = cursor.fetchone()
        
        # Claims procesados
        cursor.execute("""
            SELECT 
                COUNT(*) as total_claims,
                COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmados,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rechazados
            FROM ek_sales 
            WHERE DATE(created_at) = %s;
        """, (date,))
        
        claims_data = cursor.fetchone()
        
        return {
            "fecha": date.isoformat(),
            "leads": {
                "nuevos": leads_data[0],
                "moms": leads_data[1],
                "therapists": leads_data[2]
            },
            "mensajes": {
                "total": mensajes_data[0],
                "enviados": mensajes_data[1],
                "recibidos": mensajes_data[2],
                "entregados": mensajes_data[3],
                "leidos": mensajes_data[4],
                "tasa_entrega": round((mensajes_data[3] / max(mensajes_data[1], 1)) * 100, 1)
            },
            "ventas": {
                "confirmadas": ventas_data[0],
                "monto_total": float(ventas_data[1]),
                "promedio": float(ventas_data[2]) if ventas_data[2] else 0
            },
            "eventos": {
                "total": eventos_data[0],
                "asistieron": eventos_data[1],
                "no_show": eventos_data[2],
                "tasa_asistencia": round((eventos_data[1] / max(eventos_data[1] + eventos_data[2], 1)) * 100, 1)
            },
            "claims": {
                "total": claims_data[0],
                "confirmados": claims_data[1],
                "rechazados": claims_data[2]
            }
        }
    
    def generate_conversion_funnel(self, days: int = 30) -> Dict[str, Any]:
        """Genera funnel de conversi??n completo"""
        cursor = self.conn.cursor()
        
        # Funnel por etapas
        cursor.execute("""
            SELECT 
                stage,
                COUNT(*) as count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
            FROM ek_leads 
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY stage
            ORDER BY count DESC;
        """, (days,))
        
        stages_data = cursor.fetchall()
        
        # Conversi??n de leads a ventas
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT l.lead_id) as total_leads,
                COUNT(DISTINCT s.sale_id) as total_ventas,
                COUNT(DISTINCT s.sale_id) * 100.0 / COUNT(DISTINCT l.lead_id) as conversion_rate
            FROM ek_leads l
            LEFT JOIN ek_sales s ON l.lead_id = s.lead_id AND s.status = 'confirmed'
            WHERE l.created_at >= NOW() - INTERVAL '%s days';
        """, (days,))
        
        conversion_data = cursor.fetchone()
        
        # Conversi??n por avatar
        cursor.execute("""
            SELECT 
                l.avatar,
                COUNT(DISTINCT l.lead_id) as leads,
                COUNT(DISTINCT s.sale_id) as ventas,
                COUNT(DISTINCT s.sale_id) * 100.0 / COUNT(DISTINCT l.lead_id) as conversion_rate
            FROM ek_leads l
            LEFT JOIN ek_sales s ON l.lead_id = s.lead_id AND s.status = 'confirmed'
            WHERE l.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY l.avatar;
        """, (days,))
        
        avatar_data = cursor.fetchall()
        
        return {
            "periodo_dias": days,
            "funnel_stages": [
                {
                    "stage": row[0],
                    "count": row[1],
                    "percentage": round(row[2], 1)
                }
                for row in stages_data
            ],
            "conversion_general": {
                "total_leads": conversion_data[0],
                "total_ventas": conversion_data[1],
                "conversion_rate": round(conversion_data[2], 2)
            },
            "conversion_por_avatar": [
                {
                    "avatar": row[0],
                    "leads": row[1],
                    "ventas": row[2],
                    "conversion_rate": round(row[3], 2)
                }
                for row in avatar_data
            ]
        }
    
    def generate_hot_leads_report(self) -> Dict[str, Any]:
        """Reporte de leads calientes que necesitan atenci??n"""
        cursor = self.conn.cursor()
        
        # Leads calientes (score >= 70)
        cursor.execute("""
            SELECT 
                l.lead_id,
                l.name,
                l.phone,
                l.email,
                l.avatar,
                l.score,
                l.stage,
                l.created_at,
                COUNT(m.id) as mensajes_intercambiados
            FROM ek_leads l
            LEFT JOIN ek_ycloud_messages m ON l.lead_id = m.lead_id
            WHERE l.score >= 70
            GROUP BY l.lead_id, l.name, l.phone, l.email, l.avatar, l.score, l.stage, l.created_at
            ORDER BY l.score DESC, l.created_at DESC;
        """)
        
        hot_leads = []
        for row in cursor.fetchall():
            hot_leads.append({
                "id": str(row[0]),
                "nombre": row[1],
                "telefono": row[2],
                "email": row[3],
                "avatar": row[4],
                "score": row[5],
                "stage": row[6],
                "fecha_registro": row[7].strftime("%Y-%m-%d %H:%M"),
                "mensajes": row[8]
            })
        
        # Leads con claims pendientes
        cursor.execute("""
            SELECT 
                s.sale_id,
                l.name,
                l.phone,
                s.created_at,
                s.proof
            FROM ek_sales s
            JOIN ek_leads l ON s.lead_id = l.lead_id
            WHERE s.status = 'claimed'
            ORDER BY s.created_at DESC;
        """)
        
        pending_claims = []
        for row in cursor.fetchall():
            pending_claims.append({
                "claim_id": str(row[0]),
                "nombre": row[1],
                "telefono": row[2],
                "fecha_claim": row[3].strftime("%Y-%m-%d %H:%M"),
                "proof": row[4]
            })
        
        return {
            "hot_leads": hot_leads,
            "pending_claims": pending_claims,
            "total_hot": len(hot_leads),
            "total_pending_claims": len(pending_claims)
        }
    
    def generate_weekly_summary(self) -> Dict[str, Any]:
        """Resumen semanal para Cyn"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Lunes
        week_end = week_start + timedelta(days=6)  # Domingo
        
        cursor = self.conn.cursor()
        
        # M??tricas semanales
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT l.lead_id) as leads_semana,
                COUNT(DISTINCT CASE WHEN l.avatar = 'mother' THEN l.lead_id END) as moms,
                COUNT(DISTINCT CASE WHEN l.avatar = 'therapist' THEN l.lead_id END) as therapists,
                COUNT(DISTINCT s.sale_id) as ventas_semana,
                COALESCE(SUM(s.amount), 0) as monto_semana
            FROM ek_leads l
            LEFT JOIN ek_sales s ON l.lead_id = s.lead_id AND s.status = 'confirmed'
            WHERE DATE(l.created_at) >= %s AND DATE(l.created_at) <= %s;
        """, (week_start, week_end))
        
        semana_data = cursor.fetchone()
        
        # Eventos de la semana
        cursor.execute("""
            SELECT 
                DATE(event_start_at) as fecha,
                COUNT(*) as inscritos,
                COUNT(CASE WHEN stage = 'EVENT_ATTENDED' THEN 1 END) as asistieron
            FROM ek_leads 
            WHERE DATE(event_start_at) >= %s AND DATE(event_start_at) <= %s
            GROUP BY DATE(event_start_at)
            ORDER BY fecha;
        """, (week_start, week_end))
        
        eventos_data = cursor.fetchall()
        
        # Tendencia vs semana anterior
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT l.lead_id) as leads_semana_ant,
                COUNT(DISTINCT s.sale_id) as ventas_semana_ant,
                COALESCE(SUM(s.amount), 0) as monto_semana_ant
            FROM ek_leads l
            LEFT JOIN ek_sales s ON l.lead_id = s.lead_id AND s.status = 'confirmed'
            WHERE DATE(l.created_at) >= %s AND DATE(l.created_at) <= %s;
        """, (week_start - timedelta(days=7), week_end - timedelta(days=7)))
        
        semana_ant_data = cursor.fetchone()
        
        return {
            "semana": {
                "inicio": week_start.isoformat(),
                "fin": week_end.isoformat()
            },
            "metricas": {
                "leads": semana_data[0],
                "moms": semana_data[1],
                "therapists": semana_data[2],
                "ventas": semana_data[3],
                "monto": float(semana_data[4])
            },
            "eventos": [
                {
                    "fecha": row[0].isoformat(),
                    "inscritos": row[1],
                    "asistieron": row[2]
                }
                for row in eventos_data
            ],
            "tendencia": {
                "leads": {
                    "actual": semana_data[0],
                    "anterior": semana_ant_data[0],
                    "variacion": round(((semana_data[0] - semana_ant_data[0]) / max(semana_ant_data[0], 1)) * 100, 1)
                },
                "ventas": {
                    "actual": semana_data[3],
                    "anterior": semana_ant_data[1],
                    "variacion": round(((semana_data[3] - semana_ant_data[1]) / max(semana_ant_data[1], 1)) * 100, 1)
                },
                "monto": {
                    "actual": float(semana_data[4]),
                    "anterior": float(semana_ant_data[2]),
                    "variacion": round(((semana_data[4] - semana_ant_data[2]) / max(semana_ant_data[2], 1)) * 100, 1)
                }
            }
        }
    
    def generar_reporte_completo(self) -> Dict[str, Any]:
        """Genera todos los reportes para el dashboard"""
        return {
            "timestamp": datetime.now().isoformat(),
            "daily_report": self.generate_daily_report(),
            "conversion_funnel": self.generate_conversion_funnel(),
            "hot_leads": self.generate_hot_leads_report(),
            "weekly_summary": self.generate_weekly_summary()
        }
    
    def close(self):
        """Cierra conexi??n a BD"""
        if self.conn:
            self.conn.close()

# Funci??n principal para Windmill
def main():
    """Genera reporte completo para Cyn"""
    reports = EinsteinKidsReports()
    try:
        reporte_completo = reports.generar_reporte_completo()
        print(json.dumps(reporte_completo, indent=2, ensure_ascii=False))
    finally:
        reports.close()
