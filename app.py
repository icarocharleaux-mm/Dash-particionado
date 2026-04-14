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
    # 1. Carregar Dados - CORRIGIDO: Agora recebe os 7 valores do dados.py
    df_danos, df_faltas, df_unificado, df_mapa, df_coord, df_trat1, df_trat2 = load_data()
    
    # Unificando as tratativas para uso no painel
    df_trat = pd.concat([df_trat1, df_trat2], ignore_index=True)

    # 2. Filtros - Aplicado na base unificada
    df_filtrado = aplicar_filtros_barra_lateral(df_unificado)

    # 3. Definição das Abas (11 abas agora)
    abas = [
        "📈 Visão Geral", "👤 Motorista", "🏢 Filiais", "📦 Pedidos & Produtos", 
        "🗺️ Mapa de Calor", "📍 Rotas e Bairros", "📊 Curva ABC", "🔍 Recorrência", 
        "🚨 Fraudes & Alertas", "📋 Plano de Ação", "📈 Tendências"
    ]
    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs(abas)

    # --- ABA 1: VISÃO GERAL ---
    with aba1:
        st.subheader("📊 Visão Geral do Painel")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Ocorrências", len(df_filtrado))
        col2.metric("Qtd Total Itens", f"{df_filtrado['Quantidade'].sum():,.0f}")
        col3.metric("Motoristas Ativos", df_filtrado['Motorista'].nunique())
        col4.metric("Filiais Ofensoras", df_filtrado['Filial'].nunique())
        
        st.plotly_chart(plot_pizza_tipo_ocorrencia(df_filtrado), use_container_width=True)

    # --- ABA 2: MOTORISTA ---
    with aba2:
        st.subheader("👤 Análise por Motorista")
        st.plotly_chart(plot_top_motoristas(df_filtrado), use_container_width=True)
        st.dataframe(organizar_tabela(df_filtrado), use_container_width=True)

    # --- ABA 3: FILIAIS ---
    with aba3:
        st.subheader("🏢 Performance por Filial")
        st.plotly_chart(plot_comparativo_filial(df_filtrado), use_container_width=True)

    # --- ABA 4: PEDIDOS & PRODUTOS ---
    with aba4:
        st.subheader("📦 Detalhes de Pedidos e Produtos")
        if 'Categoria' in df_filtrado.columns:
            df_cat = df_filtrado.groupby('Categoria')['Quantidade'].sum().sort_values(ascending=False).reset_index()
            st.bar_chart(df_cat.set_index('Categoria'))
        st.dataframe(organizar_tabela(df_filtrado), use_container_width=True)

    # --- ABA 5: MAPA DE CALOR ---
    with aba5:
        st.subheader("🗺️ Mapa de Calor de Ocorrências")
        if not df_coord.empty:
            st.plotly_chart(plot_mapa_rotas(df_filtrado, df_coord), use_container_width=True)
        else:
            st.warning("Dados de coordenadas não disponíveis para gerar o mapa.")

    # --- ABA 6: ROTAS E BAIRROS ---
    with aba6:
        st.subheader("📍 Análise Geográfica por Rota")
        if not df_mapa.empty:
            st.dataframe(df_mapa, use_container_width=True)
        else:
            st.info("Informações de bairros não carregadas.")

    # --- ABA 7: CURVA ABC ---
    with aba7:
        st.subheader("📊 Curva ABC de Impacto")
        st.plotly_chart(plot_curva_abc(df_filtrado), use_container_width=True)

    # --- ABA 8: RECORRÊNCIA ---
    with aba8:
        st.subheader("🔍 Matriz de Recorrência")
        st.plotly_chart(plot_heatmap_recorrencia(df_filtrado), use_container_width=True)

    # --- ABA 9: FRAUDES & ALERTAS ---
    with aba9:
        st.subheader("🚨 Alertas de Desvios")
        # Exemplo de lógica de alerta: pedidos com alta quantidade
        alertas = df_filtrado[df_filtrado['Quantidade'] > df_filtrado['Quantidade'].quantile(0.95)]
        if not alertas.empty:
            st.warning(f"Detectados {len(alertas)} pedidos com quantidades acima do percentil 95%.")
            st.dataframe(alertas, use_container_width=True)
        else:
            st.success("Nenhum alerta crítico detectado com os filtros atuais.")

    # --- ABA 10: PLANO DE AÇÃO ---
    with aba10:
        st.subheader("📋 Plano de Ação e Diretrizes")
        st.markdown("Ações preventivas e corretivas baseadas nos dados analisados.")
        try:
            st.image("plano.jpg", use_container_width=True)
        except:
            st.info("ℹ️ Para visualizar o fluxo, certifique-se de que o arquivo 'plano.jpg' está na pasta.")

    # --- ABA 11: TENDÊNCIAS (NOVA) ---
    with aba11:
        st.subheader("📈 Análise de Tendências Externas")
        st.markdown("Visualização de dados complementares via dashboard HTML.")
        try:
            with open("dashboard (1).html", "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=800, scrolling=True)
        except FileNotFoundError:
            st.error("⚠️ O arquivo 'dashboard (1).html' não foi encontrado na pasta do projeto.")
        except Exception as e:
            st.error(f"Erro ao carregar o dashboard HTML: {e}")

except Exception as e:
    st.error(f"Erro no processamento dos dados: {e}")
    st.code(traceback.format_exc())
