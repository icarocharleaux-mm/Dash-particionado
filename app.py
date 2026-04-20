import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback
import requests
from fpdf import FPDF
from io import BytesIO
import streamlit.components.v1 as components

# --- IMPORTANDO AS CAMADAS ---
from dados import load_data
from filtros import aplicar_filtros_barra_lateral
from graficos import (plot_top_motoristas, plot_comparativo_filial, plot_pizza_tipo_ocorrencia, 
                      plot_curva_abc, plot_heatmap_recorrencia, plot_mapa_rotas)

# Configuração da Página e CSS
st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #2e4053; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; color: #555555; }
</style>
""", unsafe_allow_html=True)

def organizar_tabela(df_entrada):
    if df_entrada.empty: return df_entrada
    df = df_entrada.copy()
    colunas_iniciais = ['Cliente', 'Empresa', 'Canal', 'Motorista', 'Filial', 'Pedido', 'Quantidade', 'Rota']
    colunas_existentes = [c for c in colunas_iniciais if c in df.columns]
    outras_colunas = [c for c in df.columns if c not in colunas_existentes]
    return df[colunas_existentes + outras_colunas]

def gerar_pdf_dinamico(titulo, texto_linhas, df=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for linha in texto_linhas:
        pdf.multi_cell(0, 10, txt=str(linha))
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA PRINCIPAL ---
try:
    df_raw = load_data()
    df_filtrado = aplicar_filtros_barra_lateral(df_raw)

    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs([
        "📊 Dashboard", "📅 Motoristas", "🏢 Filiais", "🍕 Ocorrências", "📉 Curva ABC", "🔥 Recorrência", "🗺️ Rotas", "📋 Tabela", "🔗 Looker", "📜 Plano", "📈 Tendências"
    ])

    with aba1:
        # --- INCLUSÃO DA LOGO NO CABEÇALHO ---
        col_logo, col_texto = st.columns([1, 4]) 
        with col_logo:
            st.image("logo.png", use_container_width=True)
        with col_texto:
            st.title("Painel Integrado: Logística")
            st.markdown("Monitoramento de Avarias e Faltas - Projeto **A Regra é Clara**")
        st.divider()
        
        # Métricas no topo
        m1, m2, m3, m4 = st.columns(4)
        total_pedidos = len(df_filtrado)
        total_qtd = df_filtrado['Quantidade'].sum() if 'Quantidade' in df_filtrado.columns else 0
        ticket_medio = total_qtd / total_pedidos if total_pedidos > 0 else 0
        filiais_ativas = df_filtrado['Filial'].nunique() if 'Filial' in df_filtrado.columns else 0
        
        m1.metric("📦 Total de Ocorrências", f"{total_pedidos:,}")
        m2.metric("🔢 Qtd. Total Itens", f"{total_qtd:,.0f}")
        m3.metric("📈 Itens por Pedido", f"{ticket_medio:.1f}")
        m4.metric("🏢 Filiais Ofensoras", f"{filiais_ativas}")

        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🏆 Top 10 Motoristas (Ocorrências)")
            fig1 = plot_top_motoristas(df_filtrado)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("🏭 Volume por Filial")
            fig2 = plot_comparativo_filial(df_filtrado)
            st.plotly_chart(fig2, use_container_width=True)

        # Exportar Aba 1
        st.write("---\n")
        resumo_1 = [f"Total Ocorrencias: {total_pedidos}", f"Qtd Total: {total_qtd}", f"Filiais: {filiais_ativas}"]
        pdf_aba1 = gerar_pdf_dinamico("Resumo Geral - Logistica", resumo_1, None)
        st.download_button("📄 Baixar Relatório: Dashboard (PDF)", data=pdf_aba1, file_name="Resumo_Geral.pdf", mime="application/pdf", key="pdf_aba1")

    with aba2:
        st.subheader("📅 Análise Detalhada por Motorista")
        fig_mot = plot_top_motoristas(df_filtrado)
        st.plotly_chart(fig_mot, use_container_width=True)
        
    with aba3:
        st.subheader("🏢 Comparativo de Filiais")
        fig_fil = plot_comparativo_filial(df_filtrado)
        st.plotly_chart(fig_fil, use_container_width=True)

    with aba4:
        st.subheader("🍕 Tipos de Ocorrências")
        fig_pizza = plot_pizza_tipo_ocorrencia(df_filtrado)
        st.plotly_chart(fig_pizza, use_container_width=True)

    with aba5:
        st.subheader("📉 Curva ABC de Clientes Ofensores")
        fig_abc = plot_curva_abc(df_filtrado)
        st.plotly_chart(fig_abc, use_container_width=True)

    with aba6:
        st.subheader("🔥 Mapa de Calor: Recorrência Mensal")
        fig_heat = plot_heatmap_recorrencia(df_filtrado)
        st.plotly_chart(fig_heat, use_container_width=True)

    with aba7:
        st.subheader("🗺️ Visualização Geográfica de Rotas")
        fig_mapa = plot_mapa_rotas(df_filtrado)
        st.plotly_chart(fig_mapa, use_container_width=True)

    with aba8:
        st.subheader("📋 Tabela de Dados Brutos")
        df_final = organizar_tabela(df_filtrado)
        st.dataframe(df_final, use_container_width=True)
        
        # Exportar Aba 8 (CSV)
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Tabela (CSV)", data=csv, file_name="dados_logistica.csv", mime="text/csv", key="csv_aba8")

    with aba9:
        st.subheader("🔗 Relatórios Looker Studio")
        st.info("Acesse abaixo os dashboards corporativos integrados.")
        st.markdown("[Clique aqui para abrir o Looker Studio](https://lookerstudio.google.com/)")
        # Exportar Aba 9
        resumo_9 = ["Link Externo: Looker Studio corporativo."]
        pdf_aba9 = gerar_pdf_dinamico("Links Corporativos", resumo_9, None)
        st.download_button("📄 Baixar Relatório: Links (PDF)", data=pdf_aba9, file_name="Links_Looker.pdf", mime="application/pdf", key="pdf_aba9")

    with aba10:
        st.subheader("📋 Plano de Ação e Diretrizes")
        st.markdown("Siga rigorosamente as ações abaixo para mitigação de desvios e auditoria obrigatória.")
        try: st.image("plano.jpg", use_container_width=True)
        except Exception: st.error("⚠️ Arquivo 'plano.jpg' não encontrado.")
            
        # Exportar Aba 10
        st.write("---")
        resumo_10 = ["Gestao Operacional e Qualidade", "- Foco: 5 Filiais mais ofensoras", "- Data Referencia: 25/03/2026"]
        pdf_aba10 = gerar_pdf_dinamico("Plano de Acao Logistico", resumo_10, None)
        st.download_button("📄 Baixar Relatório: Plano (PDF)", data=pdf_aba10, file_name="Plano_Acao.pdf", mime="application/pdf", key="pdf_aba10")

    with aba11:
        st.subheader("📈 Análise de Tendências Logísticas")
        import os
        caminho_html = "dashboard (1).html"
        if os.path.exists(caminho_html):
            with open(caminho_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            components.html(html_content, height=800, scrolling=True)
        else:
            st.warning(f"Arquivo '{caminho_html}' não encontrado na pasta do projeto.")

except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.code(traceback.format_exc())
