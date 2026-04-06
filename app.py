import streamlit as st
import pandas as pd
import traceback

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
    colunas_iniciais = [c for c in colunas_iniciais if c in df.columns]
    outras_colunas = [c for c in df.columns if c not in colunas_iniciais and str(c).lower() not in ['transportadora', 'nome_transportadora', 'desvio_logistico', 'tipo_ocorrencia', 'mes_limpo', 'mes']]
    return df[colunas_iniciais + outras_colunas]

try:
    # 1. DADOS: Extração
    df_danos_base, df_faltas_base, df_uni_base, df_mapa_agg, df_coord_agg, df_trat1_base, df_trat2_base = load_data()

    # --- VACINA BLINDADA GERAL ---
    colunas_vitais = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Tipo_Ocorrencia', 'Pedido', 'Rota', 'Quantidade', 'Empresa', 'Canal']
    for df_limpo in [df_danos_base, df_faltas_base, df_uni_base]:
        if not df_limpo.empty:
            for col in colunas_vitais:
                if col not in df_limpo.columns: df_limpo[col] = 'Não Identificado' if col != 'Quantidade' else 0
            df_limpo['Quantidade'] = pd.to_numeric(df_limpo['Quantidade'], errors='coerce').fillna(0)
            colunas_texto = ['Cliente', 'Motorista', 'Filial', 'Categoria', 'Periodo', 'Tipo_Ocorrencia', 'Pedido', 'Rota', 'Empresa', 'Canal']
            for col in colunas_texto:
                df_limpo[col] = df_limpo[col].astype(str).str.strip()
                df_limpo.loc[df_limpo[col].str.lower() == 'nan', col] = 'Não Identificado'

    # 2. FILTROS: Aplicação
    df_uni, df_danos, df_faltas = aplicar_filtros_barra_lateral(df_uni_base, df_danos_base, df_faltas_base)

    # 3. INTERFACE GRÁFICA
    st.title("🚀 Painel Integrado de Logística")
    st.markdown("Visão consolidada cruzando dados de **Danos**, **Faltas (NC)** e **Auditoria Logística**.")
    st.divider()

    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9 = st.tabs([
        "🌐 Visão Geral", "📦 Só Danos", "📉 Só Faltas", "🎯 Curva ABC",
        "🔄 Recor. Motorista", "🔄 Recor. Cliente", "🛣️ Rotas/Mapa", "📝 Tratativas", "🚨 Fraudes"
    ])

    with aba1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ocorrências (Linhas)", len(df_uni))
        c2.metric("Ocorrências de Dano", len(df_danos))
        c3.metric("Ocorrências de Falta", len(df_faltas))
        c4.metric("Itens Afetados", int(df_uni["Quantidade"].sum()))
        st.write("---")
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("**📊 Top 10 Motoristas (Volume de Itens)**")
            fig = plot_top_motoristas(df_uni, 'Viridis')
            if fig: st.plotly_chart(fig, use_container_width=True)
        with col_dir:
            st.markdown("**⚖️ Dano x Falta (Itens)**")
            fig_p = plot_pizza_tipo_ocorrencia(df_uni)
            if fig_p: st.plotly_chart(fig_p, use_container_width=True)

    with aba2:
        if not df_danos.empty:
            st.markdown("### 📊 Análise de Danos: Top Motoristas e Filial")
            fig_m = plot_top_motoristas(df_danos, 'Blues')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            st.write("---")
            fig_f = plot_comparativo_filial(df_danos, 'Blues')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
        st.markdown("### 📋 Tabela Organizada - Danos")
        st.dataframe(organizar_tabela(df_danos), use_container_width=True)

    with aba3:
        if not df_faltas.empty:
            st.markdown("### 📊 Análise de Faltas: Top Motoristas e Filial")
            fig_m = plot_top_motoristas(df_faltas, 'Reds')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            st.write("---") 
            fig_f = plot_comparativo_filial(df_faltas, 'Reds')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
        st.markdown("### 📋 Tabela Organizada - Faltas")
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True)

    with aba4:
        st.subheader("🎯 Classificação ABC por Motorista (Reativa)")
        fig_abc, df_abc = plot_curva_abc(df_uni)
        if fig_abc:
            st.plotly_chart(fig_abc, use_container_width=True)
            st.dataframe(df_abc, use_container_width=True)
        else: st.info("Aguardando dados filtrados para calcular a Curva ABC.")

    with aba5:
        st.subheader("🔄 Histórico Mensal de Ofensores (Motoristas)")
        fig_heat_m, df_recor_m = plot_heatmap_recorrencia(df_uni, 'Motorista')
        if fig_heat_m:
            st.plotly_chart(fig_heat_m, use_container_width=True)
            st.markdown("**📋 Motoristas Reincidentes:**")
            st.dataframe(df_recor_m, use_container_width=True)
        else: st.info("Ajuste os filtros para visualizar a recorrência.")

    with aba6:
        st.subheader("🔄 Histórico Mensal de Clientes Reincidentes")
        fig_heat_c, _ = plot_heatmap_recorrencia(df_uni, 'Cliente')
        if fig_heat_c: st.plotly_chart(fig_heat_c, use_container_width=True)
        else: st.info("Nenhum cliente válido para análise na seleção atual.")

    with aba7:
        st.subheader("🗺️ Mapeamento Geográfico")
        fig_mapa, df_tab_rotas = plot_mapa_rotas(df_uni, df_mapa_agg, df_coord_agg)
        if fig_mapa:
            st.plotly_chart(fig_mapa, use_container_width=True)
            st.dataframe(df_tab_rotas, use_container_width=True)
        elif df_tab_rotas is not None:
            st.info("💡 As rotas filtradas não têm coordenadas cadastradas. Mostrando apenas a tabela:")
            st.dataframe(df_tab_rotas, use_container_width=True)
        else: st.info("Sem dados de rotas para este filtro.")

    with aba8:
        st.subheader("📝 Controle de Tratativas")
        if not df_trat1_base.empty: st.dataframe(df_trat1_base, use_container_width=True, height=250)
        if not df_trat2_base.empty: st.dataframe(df_trat2_base, use_container_width=True, height=250)

    with aba9:
        st.subheader("🚨 Dossiê de Fraudes")
        if not df_uni.empty:
            df_cli = df_uni[~df_uni['Cliente'].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
            f_vol = df_cli[df_cli['Quantidade'] >= 900].copy()
            f_vol['Motivo'] = 'Volume Crítico'
            
            df_rep = df_cli[df_cli['Quantidade'] >= 10].copy()
            cli_susp = df_rep.groupby(['Cliente', 'Quantidade']).size().reset_index(name='V')
            cli_susp = cli_susp[cli_susp['V'] > 1]
            f_rep = pd.merge(df_cli, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'])
            f_rep['Motivo'] = 'Reclamação Idêntica'
            
            alertas = pd.concat([f_vol, f_rep])
            if not alertas.empty:
                alertas = alertas.drop_duplicates(subset=['Pedido', 'Motivo'])
                alertas = alertas.loc[:, ~alertas.columns.duplicated()] 
                st.error(f"⚠️ {len(alertas)} Indícios Detectados")
                colunas_exibicao = ['Motivo', 'Cliente', 'Pedido', 'Quantidade', 'Tipo_Ocorrencia', 'Motorista', 'Filial', 'Canal']
                df_exibicao = alertas[colunas_exibicao].copy()
                total_qtd = df_exibicao['Quantidade'].sum()
                linha_total = pd.DataFrame([{'Motivo': 'TOTAL GERAL', 'Cliente': '-', 'Pedido': '-', 'Quantidade': total_qtd, 'Tipo_Ocorrencia': '-', 'Motorista': '-', 'Filial': '-', 'Canal': '-'}])
                st.dataframe(pd.concat([df_exibicao, linha_total], ignore_index=True), use_container_width=True)
            else: st.success("✅ Tudo limpo no filtro atual.")

except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.code(traceback.format_exc())
