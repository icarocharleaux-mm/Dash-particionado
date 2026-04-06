import streamlit as st
import pandas as pd
import plotly.express as px
import traceback

# --- IMPORTANDO AS CAMADAS ---
from dados import load_data
from filtros import aplicar_filtros_barra_lateral
from graficos import plot_top_motoristas, plot_comparativo_filial, plot_pizza_tipo_ocorrencia

# 1. Configuração da Página
st.set_page_config(page_title="Painel Integrado: Danos & Faltas", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #2e4053; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem; color: #555555; }
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] { font-size: 1.5rem; }
        [data-testid="stMetricLabel"] { font-size: 0.9rem; }
        .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.8rem !important; }
    }
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

    # 3. VISÃO: Interface Gráfica
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
            
            st.markdown("**Top 10 Motoristas (Itens)**")
            fig_m = plot_top_motoristas(df_danos, 'Blues')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            
            st.write("---")
            
            st.markdown("**Comparativo por Filial (Itens)**")
            fig_f = plot_comparativo_filial(df_danos, 'Blues')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
                
        st.markdown("### 📋 Tabela Organizada - Danos")
        st.dataframe(organizar_tabela(df_danos), use_container_width=True)

    with aba3:
        if not df_faltas.empty:
            st.markdown("### 📊 Análise de Faltas: Top Motoristas e Filial")
            
            st.markdown("**Top 10 Motoristas (Itens)**")
            fig_m = plot_top_motoristas(df_faltas, 'Reds')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            
            st.write("---") 
            
            st.markdown("**Comparativo por Filial (Itens)**")
            fig_f = plot_comparativo_filial(df_faltas, 'Reds')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)

        st.markdown("### 📋 Tabela Organizada - Faltas")
        st.dataframe(organizar_tabela(df_faltas), use_container_width=True)

    with aba4:
        st.subheader("🎯 Classificação ABC por Motorista (Reativa)")
        if not df_uni.empty:
            abc = df_uni.groupby('Motorista')['Quantidade'].sum().sort_values(ascending=False).reset_index()
            abc['SomaAcum'] = abc['Quantidade'].cumsum()
            abc['PercAcum'] = 100 * abc['SomaAcum'] / abc['Quantidade'].sum()
            abc['Classe'] = abc['PercAcum'].apply(lambda x: 'A (Crítico - 70%)' if x <= 70 else ('B (Atenção - 20%)' if x <= 90 else 'C (Normal - 10%)'))
            st.plotly_chart(px.bar(abc, x='Motorista', y='Quantidade', color='Classe', color_discrete_map={'A (Crítico - 70%)':'#d62728','B (Atenção - 20%)':'#ff7f0e','C (Normal - 10%)':'#2ca02c'}), use_container_width=True)
            st.dataframe(abc, use_container_width=True)
        else: 
            st.info("Aguardando dados filtrados para calcular a Curva ABC.")

    with aba5:
        st.subheader("🔄 Histórico Mensal de Ofensores (Motoristas)")
        if not df_uni.empty:
            df_hist = df_uni.groupby(['Motorista', 'Periodo']).size().reset_index(name='Casos')
            df_pivot = df_hist.pivot_table(index='Motorista', columns='Periodo', values='Casos', fill_value=0)
            
            meses_ref = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            colunas_existentes = [m for m in meses_ref if m in df_pivot.columns]
            df_pivot = df_pivot[colunas_existentes]
            
            df_pivot['Total_Filtro'] = df_pivot.sum(axis=1)
            df_pivot = df_pivot.sort_values('Total_Filtro', ascending=False).drop(columns=['Total_Filtro'])

            fig_heat = px.imshow(df_pivot.head(25), text_auto=True, aspect="auto", color_continuous_scale='YlOrRd', labels=dict(x="Mês", y="Motorista", color="Ocorrências"))
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.markdown("**📋 Motoristas Reincidentes (Qtd de meses com ocorrência):**")
            recor_resumo = df_uni.groupby('Motorista')['Periodo'].nunique().sort_values(ascending=False).reset_index()
            recor_resumo.columns = ['Motorista', 'Meses com Problemas']
            st.dataframe(recor_resumo[recor_resumo['Meses com Problemas'] > 1], use_container_width=True)
        else: 
            st.info("Ajuste os filtros para visualizar a recorrência.")

    with aba6:
        st.subheader("🔄 Histórico Mensal de Clientes Reincidentes")
        if not df_uni.empty:
            df_cli_rec = df_uni[~df_uni['Cliente'].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
            if not df_cli_rec.empty:
                df_hist_cli = df_cli_rec.groupby(['Cliente', 'Periodo']).size().reset_index(name='Casos')
                df_pivot_cli = df_hist_cli.pivot_table(index='Cliente', columns='Periodo', values='Casos', fill_value=0)
                
                meses_ref = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                colunas_meses_cli = [m for m in meses_ref if m in df_pivot_cli.columns]
                df_pivot_cli = df_pivot_cli[colunas_meses_cli]
                
                df_pivot_cli['Total'] = df_pivot_cli.sum(axis=1)
                st.plotly_chart(px.imshow(df_pivot_cli.sort_values('Total', ascending=False).drop(columns=['Total']).head(25), text_auto=True, aspect="auto", color_continuous_scale='YlOrRd', labels=dict(x="Mês", y="Cliente", color="Ocorrências")), use_container_width=True)
            else:
                st.info("Nenhum cliente válido para análise na seleção atual.")
        else:
            st.info("Ajuste os filtros para visualizar a recorrência.")

    with aba7:
        st.subheader("🗺️ Mapeamento Geográfico")
        df_rotas = df_uni[~df_uni['Rota'].str.upper().isin(['N/A', 'NAN', 'NÃO IDENTIFICADO', ''])]
        
        if not df_rotas.empty:
            tabela_r = df_rotas.groupby('Rota').size().reset_index(name='Total_Geral')
            
            tabela_r['Rota'] = tabela_r['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            if not df_coord_agg.empty and 'Rota' in df_coord_agg.columns:
                df_coord_agg['Rota'] = df_coord_agg['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            else:
                df_coord_agg = pd.DataFrame(columns=['Rota', 'LATITUDE', 'LONGITUDE'])
                
            if not df_mapa_agg.empty and 'Rota' in df_mapa_agg.columns:
                df_mapa_agg['Rota'] = df_mapa_agg['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            else:
                df_mapa_agg = pd.DataFrame(columns=['Rota', 'Setor', 'Bairro'])
            
            tabela_final = pd.merge(tabela_r, df_mapa_agg, on='Rota', how='left')
            tabela_final = pd.merge(tabela_final, df_coord_agg, on='Rota', how='left')
            
            df_mapa_plot = tabela_final.dropna(subset=['LATITUDE', 'LONGITUDE'])
            if not df_mapa_plot.empty:
                st.plotly_chart(px.scatter_mapbox(df_mapa_plot, lat="LATITUDE", lon="LONGITUDE", size="Total_Geral", color="Total_Geral", hover_name="Setor", hover_data=["Rota", "Bairro"], zoom=7, mapbox_style="carto-positron"), use_container_width=True)
            else:
                st.info("💡 As rotas filtradas não têm coordenadas no 'base_coordenadas.csv'.")
                
            st.dataframe(tabela_final[['Rota', 'Setor', 'Bairro', 'Total_Geral']].sort_values('Total_Geral', ascending=False), use_container_width=True)
        else:
            st.info("Sem dados de rotas para este filtro.")

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
                
                linha_total = pd.DataFrame([{
                    'Motivo': 'TOTAL GERAL',
                    'Cliente': '-',
                    'Pedido': '-',
                    'Quantidade': total_qtd,
                    'Tipo_Ocorrencia': '-',
                    'Motorista': '-',
                    'Filial': '-',
                    'Canal': '-'
                }])
                
                df_final = pd.concat([df_exibicao, linha_total], ignore_index=True)
                st.dataframe(df_final, use_container_width=True)
            else: 
                st.success("✅ Tudo limpo no filtro atual.")

except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.code(traceback.format_exc())