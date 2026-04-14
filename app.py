import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import traceback
import requests
from fpdf import FPDF
from io import BytesIO
import streamlit.components.v1 as components  # Para renderizar o HTML das Tendências

# --- IMPORTANDO AS CAMADAS ---
from dados import load_data
from filtros import aplicar_filtros_barra_lateral
from graficos import (plot_top_motoristas, plot_comparativo_filial, plot_pizza_tipo_ocorrencia, 
                      plot_curva_abc, plot_heatmap_recorrencia, plot_mapa_rotas)

# Configuração da Página
st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")

# CSS para melhorar a estética
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

def gerar_pdf_dinamico(titulo, resumo_linhas, df_tabela=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, titulo, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for linha in resumo_linhas:
        pdf.multi_cell(0, 10, linha)
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

try:
    # 1. Carregar Dados
    df_danos, df_trat, df_coord, df_mapa = load_data()
    
    # 2. Filtros
    df_filtrado = aplicar_filtros_barra_lateral(df_danos)

    # 3. Definição das Abas
    abas = [
        "📈 Visão Geral", "👤 Motorista", "🏢 Filiais", "📦 Pedidos & Produtos", 
        "🗺️ Mapa de Calor", "📍 Rotas e Bairros", "📊 Curva ABC", "🔍 Recorrência", 
        "🚨 Fraudes & Alertas", "📋 Plano de Ação", "📈 Tendências"
    ]
    # Criando as 11 variáveis para as 11 abas
    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs(abas)

    with aba1:
        st.subheader("📊 Visão Geral do Painel")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Ocorrências", len(df_filtrado))
        col2.metric("Qtd Total Itens", f"{df_filtrado['quantidade'].sum():,.0f}")
        col3.metric("Motoristas Ativos", df_filtrado['motorista'].nunique())
        col4.metric("Filiais Ofensoras", df_filtrado['filial'].nunique())
        st.plotly_chart(plot_pizza_tipo_ocorrencia(df_filtrado), use_container_width=True)

    with aba2:
        st.subheader("👤 Análise por Motorista")
        st.plotly_chart(plot_top_motoristas(df_filtrado), use_container_width=True)
        st.dataframe(organizar_tabela(df_filtrado), use_container_width=True)

    with aba3:
        st.subheader("🏢 Performance por Filial")
        st.plotly_chart(plot_comparativo_filial(df_filtrado), use_container_width=True)

    with aba4:
        st.subheader("📦 Detalhes de Pedidos e Produtos")
        df_prod = df_filtrado.groupby('produto')['quantidade'].sum().sort_values(ascending=False).reset_index()
        st.bar_chart(df_prod.set_index('produto'))

    with aba5:
        st.subheader("🗺️ Mapa de Calor de Ocorrências")
        if not df_coord.empty:
            st.plotly_chart(plot_mapa_rotas(df_filtrado, df_coord), use_container_width=True)
        else:
            st.warning("Dados de coordenadas não disponíveis.")

    with aba6:
        st.subheader("📍 Análise de Rotas e Bairros")
        st.dataframe(df_mapa, use_container_width=True)

    with aba7:
        st.subheader("📊 Curva ABC de Impacto")
        st.plotly_chart(plot_curva_abc(df_filtrado), use_container_width=True)

    with aba8:
        st.subheader("🔍 Recorrência e Frequência")
        st.plotly_chart(plot_heatmap_recorrencia(df_filtrado), use_container_width=True)

    with aba9:
        st.subheader("🚨 Fraudes & Alertas do Sistema")
        alertas = df_filtrado[df_filtrado['quantidade'] > 10] # Exemplo de lógica
        st.table(alertas.head(10))

    with aba10:
        st.subheader("📋 Plano de Ação e Diretrizes")
        st.markdown("Siga as diretrizes para mitigação de desvios.")
        try:
            st.image("plano.jpg", use_container_width=True)
        except:
            st.info("ℹ️ Adicione o arquivo 'plano.jpg' na pasta para visualização da imagem.")

    # --- NOVA ABA INTEGRADA ---
    with aba11:
        st.subheader("📈 Análise de Tendências Externas")
        try:
            with open("dashboard (1).html", "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=800, scrolling=True)
        except FileNotFoundError:
            st.error("⚠️ O arquivo 'dashboard (1).html' não foi encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar dashboard: {e}")

except Exception as e:
    st.error(f"Erro crítico no sistema: {e}")
    st.code(traceback.format_exc())
