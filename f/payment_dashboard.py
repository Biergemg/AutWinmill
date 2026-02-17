# 🏢 SISTEMA DE CONTROL DE PAGOS - Modelo GOOGLE
# Dashboard para monitorear todos los clientes y sus pagos

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from f.payment_control_system import PaymentControlSystem

def main():
    st.set_page_config(
        page_title="🏢 Control de Pagos - SaaS Dashboard",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("🏢 Sistema de Control de Pagos - Modelo SaaS")
    st.markdown("### 💼 Gestión Multi-Cliente con Control de Suscripciones")
    
    # Inicializar sistema de control
    control = PaymentControlSystem()
    
    # Sidebar - Información general
    with st.sidebar:
        st.header("📊 Dashboard General")
        
        # Obtener estadísticas
        clients_status = control.check_all_clients()
        total_clients = len(clients_status)
        active_clients = sum(1 for c in clients_status if c['status'] == 'active')
        suspended_clients = sum(1 for c in clients_status if c['status'] == 'suspended')
        overdue_clients = sum(1 for c in clients_status if c.get('days_overdue', 0) > 0)
        
        st.metric("👥 Total Clientes", total_clients)
        st.metric("✅ Activos", active_clients)
        st.metric("🚫 Suspendidos", suspended_clients)
        st.metric("⚠️ Vencidos", overdue_clients)
        
        # Ingresos mensuales proyectados
        monthly_revenue = sum(c.get('monthly_fee', 0) for c in clients_status if c['status'] == 'active')
        st.metric("💰 Ingresos Mensuales", f"${monthly_revenue:,.2f}")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "👥 Clientes", "💳 Pagos", "⚙️ Configuración"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de estado de clientes
            status_data = pd.DataFrame([
                {'Estado': 'Activos', 'Cantidad': active_clients, 'Color': '#00FF00'},
                {'Estado': 'Suspendidos', 'Cantidad': suspended_clients, 'Color': '#FF0000'},
                {'Estado': 'Vencidos', 'Cantidad': overdue_clients, 'Color': '#FFA500'}
            ])
            
            fig_status = px.pie(status_data, values='Cantidad', names='Estado', 
                               title='📊 Estado de Clientes',
                               color='Estado', color_discrete_map={'Activos': '#00FF00', 
                                                                   'Suspendidos': '#FF0000', 
                                                                   'Vencidos': '#FFA500'})
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Gráfico de ingresos proyectados
            revenue_data = []
            for i in range(12):
                date = datetime.now() + timedelta(days=30*i)
                revenue = monthly_revenue
                revenue_data.append({'Mes': date.strftime('%Y-%m'), 'Ingresos': revenue})
            
            fig_revenue = px.line(revenue_data, x='Mes', y='Ingresos', 
                                title='📈 Proyección de Ingresos',
                                markers=True)
            fig_revenue.update_traces(line_color='#00FF00', line_width=3)
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        # Tabla de clientes con problemas
        st.subheader("⚠️ Clientes que Requieren Atención")
        
        problem_clients = []
        for client in clients_status:
            if client.get('days_overdue', 0) > 0 or client['status'] == 'suspended':
                problem_clients.append({
                    'Cliente': client['client'],
                    'Puerto': client['port'],
                    'Estado': client['status'],
                    'Días Vencidos': client.get('days_overdue', 0),
                    'Próximo Pago': client['next_payment']
                })
        
        if problem_clients:
            df_problems = pd.DataFrame(problem_clients)
            st.dataframe(df_problems, use_container_width=True)
        else:
            st.success("✅ Todos los clientes están al día con sus pagos")
    
    with tab2:
        st.header("👥 Gestión de Clientes")
        
        # Tabla completa de clientes
        clients_data = []
        for client in clients_status:
            clients_data.append({
                'Cliente': client['client'],
                'Puerto': client['port'],
                'Estado': client['status'],
                'Último Pago': client['last_payment'],
                'Próximo Pago': client['next_payment'],
                'Días Vencidos': client.get('days_overdue', 0),
                'Acciones': 'Ver Detalles'
            })
        
        df_clients = pd.DataFrame(clients_data)
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect("Filtrar por Estado", 
                                         ['active', 'suspended', 'cancelled'],
                                         default=['active', 'suspended'])
        
        with col2:
            overdue_filter = st.checkbox("Mostrar solo vencidos", False)
        
        # Aplicar filtros
        if status_filter:
            df_clients = df_clients[df_clients['Estado'].isin(status_filter)]
        
        if overdue_filter:
            df_clients = df_clients[df_clients['Días Vencidos'] > 0]
        
        st.dataframe(df_clients, use_container_width=True)
        
        # Acciones por cliente
        selected_client = st.selectbox("Seleccionar Cliente para Acciones", 
                                     [c['client'] for c in clients_status])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💳 Registrar Pago", type="primary"):
                amount = st.number_input("Monto del pago", min_value=0.0, value=297.0)
                if st.button("Confirmar Pago"):
                    success = control.process_payment(selected_client, amount)
                    if success:
                        st.success(f"✅ Pago registrado para {selected_client}")
                        st.rerun()
        
        with col2:
            if st.button("📧 Enviar Recordatorio"):
                success = control.send_payment_reminder(selected_client)
                if success:
                    st.success(f"📧 Recordatorio enviado a {selected_client}")
        
        with col3:
            if st.button("🚫 Suspender Cliente", type="secondary"):
                if st.button("⚠️ Confirmar Suspensión"):
                    success = control.suspend_client(selected_client)
                    if success:
                        st.error(f"🚫 Cliente {selected_client} suspendido")
                        st.rerun()
    
    with tab3:
        st.header("💳 Historial de Pagos")
        
        # Simular datos de pagos recientes
        payments_data = []
        for client in clients_status:
            # Simular últimos 6 pagos
            for i in range(6):
                payment_date = datetime.now() - timedelta(days=30*i)
                payments_data.append({
                    'Cliente': client['client'],
                    'Fecha': payment_date.strftime('%Y-%m-%d'),
                    'Monto': 297.0,
                    'Método': 'Stripe',
                    'Estado': 'Completado'
                })
        
        df_payments = pd.DataFrame(payments_data)
        
        # Gráfico de pagos por mes
        df_payments['Mes'] = pd.to_datetime(df_payments['Fecha']).dt.to_period('M')
        monthly_payments = df_payments.groupby('Mes')['Monto'].sum().reset_index()
        monthly_payments['Mes'] = monthly_payments['Mes'].astype(str)
        
        fig_payments = px.bar(monthly_payments, x='Mes', y='Monto',
                            title='💰 Pagos Mensuales',
                            color='Monto', color_continuous_scale='greens')
        st.plotly_chart(fig_payments, use_container_width=True)
        
        # Tabla de pagos
        st.dataframe(df_payments, use_container_width=True)
    
    with tab4:
        st.header("⚙️ Configuración del Sistema")
        
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Configuración General")
            grace_days = st.number_input("Días de gracia para pagos", min_value=1, max_value=30, value=3)
            currency = st.selectbox("Moneda", ["USD", "EUR", "MXN"], index=0)
            
            if st.button("💾 Guardar Configuración"):
                st.success("✅ Configuración guardada")
        
        with col2:
            st.subheader("🔔 Notificaciones")
            email_notifications = st.checkbox("Enviar emails de recordatorio", value=True)
            auto_suspend = st.checkbox("Suspender automáticamente por falta de pago", value=True)
            
            if st.button("🔄 Actualizar Preferencias"):
                st.success("✅ Preferencias actualizadas")
        
        # Estado del sistema
        st.subheader("📊 Estado del Sistema")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Verificar contenedores Docker
            try:
                import subprocess
                result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                      capture_output=True, text=True)
                containers = result.stdout
                
                st.metric("🐳 Contenedores Activos", len(containers.split('\n'))-2)  # -2 por headers
                st.text("Estado de contenedores:")
                st.code(containers, language="bash")
            except:
                st.warning("Docker no disponible")
        
        with col2:
            # Uso de recursos (simulado)
            cpu_usage = 45
            memory_usage = 67
            disk_usage = 23
            
            st.metric("💻 CPU", f"{cpu_usage}%")
            st.metric("💾 Memoria", f"{memory_usage}%")
            st.metric("💿 Disco", f"{disk_usage}%")
        
        with col3:
            # Logs recientes (simulado)
            st.text("📋 Logs recientes:")
            logs = [
                f"{datetime.now().strftime('%H:%M:%S')} - Sistema iniciado",
                f"{(datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S')} - Cliente Cyn verificado",
                f"{(datetime.now() - timedelta(minutes=10)).strftime('%H:%M:%S')} - Pago procesado",
                f"{(datetime.now() - timedelta(minutes=15)).strftime('%H:%M:%S')} - Sistema funcionando correctamente"
            ]
            st.code("\n".join(logs), language="text")

if __name__ == "__main__":
    main()