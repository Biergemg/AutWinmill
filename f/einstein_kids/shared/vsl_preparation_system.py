"""
Preparación para Escalación VSL (Fase 2)
Cuando la masterclass en vivo esté consolidada
"""

import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class VSLTransitionConfig:
    """Configuración para transición de masterclass en vivo a VSL"""
    
    # Triggers de decisión
    live_attendance_rate: float = 0.0  # % de asistencia actual
    conversion_rate_live: float = 0.0  # % de conversión actual
    lead_volume: int = 0  # Leads por mes
    operational_cost: float = 0.0  # Costo de operar en vivo
    
    # Umbrales para VSL
    min_attendance_rate: float = 0.60  # 60% show-up rate
    min_conversion_rate: float = 0.08   # 8% conversión
    min_lead_volume: int = 500  # 500 leads/mes
    max_operational_cost_ratio: float = 0.25  # 25% del revenue

class VSLPreparationSystem:
    """
    Sistema que prepara la escalación a VSL cuando la masterclass en vivo esté consolidada
    """
    
    def __init__(self):
        self.performance_metrics = {}
        self.vsl_ready_checklist = {}
        self.transition_triggers = {}
    
    def analyze_live_performance(self, months_data: List[Dict]) -> Dict:
        """Analiza si está lista para transición a VSL"""
        
        analysis = {
            "ready_for_vsl": False,
            "metrics_summary": {},
            "recommendations": [],
            "vsl_benefits": [],
            "risks": []
        }
        
        # Calcular métricas promedio
        avg_attendance = sum(m['attendance_rate'] for m in months_data) / len(months_data)
        avg_conversion = sum(m['conversion_rate'] for m in months_data) / len(months_data)
        avg_leads = sum(m['total_leads'] for m in months_data) / len(months_data)
        avg_revenue = sum(m['revenue'] for m in months_data) / len(months_data)
        avg_cost = sum(m['operational_cost'] for m in months_data) / len(months_data)
        
        analysis["metrics_summary"] = {
            "avg_attendance_rate": avg_attendance,
            "avg_conversion_rate": avg_conversion,
            "avg_monthly_leads": avg_leads,
            "avg_monthly_revenue": avg_revenue,
            "avg_operational_cost": avg_cost,
            "cost_ratio": avg_cost / avg_revenue if avg_revenue > 0 else 1
        }
        
        # Evaluar readiness para VSL
        config = VSLTransitionConfig(
            live_attendance_rate=avg_attendance,
            conversion_rate_live=avg_conversion,
            lead_volume=int(avg_leads),
            operational_cost=avg_cost
        )
        
        analysis["ready_for_vsl"] = self.check_vsl_readiness(config)
        
        if analysis["ready_for_vsl"]:
            analysis["vsl_benefits"] = self.calculate_vsl_benefits(avg_attendance, avg_conversion, avg_leads)
            analysis["transition_plan"] = self.create_transition_plan()
        else:
            analysis["recommendations"] = self.get_optimization_recommendations(config)
            analysis["risks"] = self.get_transition_risks(config)
        
        return analysis
    
    def check_vsl_readiness(self, config: VSLTransitionConfig) -> bool:
        """Verifica si cumple criterios para VSL"""
        
        return (
            config.live_attendance_rate >= config.min_attendance_rate and
            config.conversion_rate_live >= config.min_conversion_rate and
            config.lead_volume >= config.min_lead_volume and
            (config.operational_cost / (config.lead_volume * 1997 * config.conversion_rate_live)) <= config.max_operational_cost_ratio
        )
    
    def calculate_vsl_benefits(self, attendance_rate: float, conversion_rate: float, monthly_leads: float) -> List[Dict]:
        """Calcula beneficios de transición a VSL"""
        
        benefits = []
        
        # Beneficio 1: Mayor alcance
        vsl_capacity = 5000  # VSL puede manejar 5000 vs 100 en vivo
        potential_reach_increase = (vsl_capacity / 100 - 1) * 100
        
        benefits.append({
            "benefit": "Capacidad ilimitada",
            "current": "100 personas máx por evento",
            "vsl": "5000+ personas simultáneas",
            "impact": f"+{potential_reach_increase:.0f}% de alcance"
        })
        
        # Beneficio 2: Frecuencia diaria
        current_monthly_events = 4  # 1 por semana
        vsl_monthly_capacity = 30   # 1 por día
        
        benefits.append({
            "benefit": "Frecuencia de eventos",
            "current": f"{current_monthly_events} eventos/mes",
            "vsl": f"{vsl_monthly_capacity} eventos/mes",
            "impact": f"+{(vsl_monthly_capacity/current_monthly_events - 1)*100:.0f}% más oportunidades"
        })
        
        # Beneficio 3: Reducción de costos operativos
        current_monthly_cost = 5000  # Costo de operar 4 eventos en vivo
        vsl_monthly_cost = 500       # Costo de operar VSL
        
        benefits.append({
            "benefit": "Costos operativos",
            "current": f"${current_monthly_cost}/mes",
            "vsl": f"${vsl_monthly_cost}/mes",
            "impact": f"-{((current_monthly_cost - vsl_monthly_cost) / current_monthly_cost * 100):.0f}% ahorro"
        })
        
        # Beneficio 4: Mejor show-up rate
        current_showup = attendance_rate  # Ej: 65%
        vsl_showup_potential = 0.75        # VSL típicamente 70-80%
        
        benefits.append({
            "benefit": "Show-up rate",
            "current": f"{attendance_rate*100:.0f}%",
            "vsl": f"{vsl_showup_potential*100:.0f}%",
            "impact": f"+{(vsl_showup_potential - attendance_rate)*100:.0f}% asistencia"
        })
        
        return benefits
    
    def create_transition_plan(self) -> Dict:
        """Crea plan de transición gradual a VSL"""
        
        return {
            "phase_1": {
                "duration": "1-2 meses",
                "action": "Híbrido: 50% en vivo, 50% VSL",
                "objective": "Validar VSL sin perder revenue"
            },
            "phase_2": {
                "duration": "1 mes", 
                "action": "70% VSL, 30% en vivo",
                "objective": "Escalar VSL, mantener vivo para VIP"
            },
            "phase_3": {
                "duration": "Continuo",
                "action": "90% VSL, 10% en vivo mensual",
                "objective": "VSL principal, vivo para comunidad"
            },
            "vsl_development": {
                "timeline": "6-8 semanas",
                "tasks": [
                    "Grabar VSL con Cyn (2 semanas)",
                    "Editar y post-producción (2 semanas)", 
                    "Integrar tracking conductual (1 semana)",
                    "Testing y optimización (2 semanas)"
                ]
            }
        }
    
    def get_optimization_recommendations(self, config: VSLTransitionConfig) -> List[str]:
        """Recomendaciones para mejorar antes de VSL"""
        
        recommendations = []
        
        if config.live_attendance_rate < config.min_attendance_rate:
            recommendations.append(f"Mejorar show-up rate: {config.live_attendance_rate*100:.0f}% → {config.min_attendance_rate*100:.0f}%")
        
        if config.conversion_rate_live < config.min_conversion_rate:
            recommendations.append(f"Optimizar conversión: {config.conversion_rate_live*100:.0f}% → {config.min_conversion_rate*100:.0f}%")
        
        if config.lead_volume < config.min_lead_volume:
            recommendations.append(f"Aumentar volumen: {config.lead_volume} → {config.min_lead_volume} leads/mes")
        
        return recommendations
    
    def get_transition_risks(self, config: VSLTransitionConfig) -> List[Dict]:
        """Identifica riesgos de transición temprana"""
        
        risks = []
        
        if config.live_attendance_rate < 0.50:
            risks.append({
                "risk": "Show-up rate bajo",
                "impact": "VSL podría tener peor asistencia",
                "mitigation": "Mejorar secuencia de recordatorios antes de VSL"
            })
        
        if config.conversion_rate_live < 0.05:
            risks.append({
                "risk": "Conversión baja", 
                "impact": "VSL no necesariamente mejorará conversión",
                "mitigation": "Optimizar oferta y presentación antes de grabar VSL"
            })
        
        if config.lead_volume < 300:
            risks.append({
                "risk": "Volumen insuficiente",
                "impact": "Inversión en VSL no se justifica",
                "mitigation": "Escalar adquisición de leads primero"
            })
        
        return risks
    
    def prepare_vsl_content_structure(self) -> Dict:
        """Prepara estructura de contenido para futuro VSL"""
        
        return {
            "vsl_structure": {
                "hook_0_3_seconds": "¿Sabías que el 90% de mamás estimulan mal a sus bebés?",
                "problem_3_30": "3 errores comunes que retrasan desarrollo",
                "solution_30_45": "Método científico de estimulación temprana",
                "mechanism_45_60": "Cómo funciona el neurodesarrollo infantil",
                "proof_60_75": "Casos de éxito con bebés de diferentes edades",
                "offer_75_90": "Godfather Offer con stack de valor",
                "scarcity_90_100": "Spots limitados y urgencia real"
            },
            "personalization_points": [
                "Edad del bebé (0-3, 4-6, 7-12, 12+ meses)",
                "Nombre de la mamá",
                "Tipo de preocupación principal (motor, cognitivo, social)",
                "Experiencia previa con estimulación"
            ],
            "tracking_moments": [
                "Minuto 3: Hook engagement",
                "Minuto 15: Problem acknowledgment", 
                "Minuto 30: Solution interest",
                "Minuto 45: Mechanism understanding",
                "Minuto 60: Proof validation",
                "Minuto 75: Offer presentation",
                "Minuto 90: Scarcity trigger"
            ]
        }
    
    def create_performance_dashboard(self) -> Dict:
        """Crea dashboard para monitorear métricas clave"""
        
        return {
            "key_metrics": {
                "live_performance": [
                    "Show-up rate (target: 60%+)",
                    "Conversion rate (target: 8%+)", 
                    "Engagement score promedio",
                    "Godfather Offer acceptance"
                ],
                "vsl_readiness": [
                    "Volumen de leads mensual",
                    "Costo operativo vs revenue",
                    "Consistencia de métricas (3+ meses)",
                    "Feedback de clientes"
                ]
            },
            "alerts": {
                "green": "Listo para VSL - métricas óptimas",
                "yellow": "Cerca del umbral - optimizar antes de VSL", 
                "red": "No listo para VSL - mejorar métricas primero"
            }
        }