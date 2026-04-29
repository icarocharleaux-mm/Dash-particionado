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
                      plot_curva_abc, plot_heatmap_recorrencia, plot_mapa_rotas,
                      plot_evolucao_temporal) 
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
    outras_colunas = [c for c in df.columns if c not in colunas_iniciais and str(c).lower() not in ['transportadora', 'nome_transportadora', 'desvio_logistico', 'tipo_ocorrencia', 'mes_limpo', 'mes', 'data_filtro']]
    return df[colunas_iniciais + outras_colunas]

# --- NOVA FUNÇÃO DE PDF DINÂMICO ---
def gerar_pdf_dinamico(titulo, linhas_resumo, df_tabela=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho do PDF
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, str(titulo).encode('latin-1', 'ignore').decode('latin-1'), ln=True, align="C")
    pdf.ln(5)
    
    # Linhas de Resumo/Contexto
    pdf.set_font("helvetica", "", 12)
    for linha in linhas_resumo:
        pdf.cell(0, 8, str(linha).encode('latin-1', 'ignore').decode('latin-1'), ln=True)
    pdf.ln(5)
    
    # Tabela com Top Registros da respectiva aba
    if df_tabela is not None and not df_tabela.empty:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Detalhamento (Amostra dos Principais Registros)", ln=True)
        pdf.set_font("helvetica", "B", 9)
        
        # Pega as primeiras 4 colunas para caber na largura da folha A4
        colunas = list(df_tabela.columns)[:4] 
        cabecalho = " | ".join([str(c)[:18] for c in colunas])
        pdf.cell(0, 8, cabecalho.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        
        pdf.set_font("helvetica", "", 9)
        # Limita a 20 linhas para não estourar páginas desnecessariamente
        for _, row in df_tabela.head(20).iterrows(): 
            valores = [str(row[c])[:18] for c in colunas]
            linha_val = " | ".join(valores)
            pdf.cell(0, 6, linha_val.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
            
    return bytes(pdf.output())

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

    aba1, aba2, aba3, aba4, aba5, aba6, aba7, aba8, aba9, aba10, aba11 = st.tabs([
        "🌐 Visão Geral", "📦 Só Danos", "📉 Só Faltas", "🎯 Curva ABC",
        "🔄 Recor. Motorista", "🔄 Recor. Cliente", "🛣️ Rotas/Mapa", "📝 Tratativas", "🚨 Fraudes", "📋 Plano de Ação", "📈 Tendências"
    ])

    with aba1:
        total_ocorrencias = len(df_uni)
        if total_ocorrencias > 0:
            taxa_dano = len(df_danos) / total_ocorrencias
            taxa_falta = len(df_faltas) / total_ocorrencias
            media_itens_por_ocorrencia = df_uni["Quantidade"].sum() / total_ocorrencias
        else:
            taxa_dano = 0
            taxa_falta = 0
            media_itens_por_ocorrencia = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Ocorrências", total_ocorrencias)
        c2.metric("Ocorrências de Dano", len(df_danos), f"{taxa_dano:.1%} do Total", delta_color="off")
        c3.metric("Ocorrências de Falta", len(df_faltas), f"{taxa_falta:.1%} do Total", delta_color="off")
        c4.metric("Média Itens/Ocorrência", f"{media_itens_por_ocorrencia:.1f}")
        
        st.write("---")
        
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("**📊 Top 10 Motoristas (Volume de Itens)**")
            if not df_uni.empty:
                ranking = df_uni.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
                filial_map_geral = df_uni.groupby("Motorista")["Filial"].agg(lambda x: x.value_counts().index[0] if not x.empty else "N/A").to_dict()
                ranking["Filial"] = ranking["Motorista"].map(filial_map_geral)
                
                fig = px.bar(ranking, x='Quantidade', y='Motorista', orientation='h', 
                             color='Quantidade', color_continuous_scale='Viridis',
                             hover_data=['Filial'])
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
        with col_dir:
            st.markdown("**⚖️ Dano x Falta (Itens)**")
            if not df_uni.empty:
                pizza = df_uni.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
                fig_p = px.pie(pizza, names='Tipo_Ocorrencia', values='Quantidade', hole=0.4, color_discrete_map={'Dano':'#1f77b4', 'Falta':'#d62728'})
                st.plotly_chart(fig_p, use_container_width=True)

        # ==========================================
        # NOVO GRÁFICO DE CATEGORIAS - VISÃO GERAL
        # ==========================================
        st.write("---")
        st.markdown("**🏷️ Top 10 Categorias Afetadas (Geral)**")
        if not df_uni.empty and 'Categoria' in df_uni.columns:
            cat_ranking = df_uni.groupby('Categoria')['Quantidade'].sum().nlargest(10).reset_index()
            fig_cat1 = px.bar(cat_ranking, x='Quantidade', y='Categoria', orientation='h', 
                              color='Quantidade', color_continuous_scale='Viridis', text_auto='.0f')
            fig_cat1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_cat1, use_container_width=True)

        st.write("---")
        with st.expander("🔎 Ferramenta de Investigação: Explorar Dados Detalhados (Drill Down)"):
            if not df_uni.empty: st.dataframe(organizar_tabela(df_uni), use_container_width=True)
            else: st.info("Nenhum dado encontrado para os filtros atuais.")
                
        # Exportar Aba 1
        st.write("---")
        top_geral = df_uni.groupby('Motorista')['Quantidade'].sum().nlargest(15).reset_index() if not df_uni.empty else None
        resumo_1 = [f"Total Geral: {total_ocorrencias} ocorrencias", f"Danos: {len(df_danos)}", f"Faltas: {len(df_faltas)}"]
        pdf_aba1 = gerar_pdf_dinamico("Relatorio - Visao Geral", resumo_1, top_geral)
        st.download_button("📄 Baixar Relatório: Visão Geral (PDF)", data=pdf_aba1, file_name="Visao_Geral.pdf", mime="application/pdf", key="pdf_aba1")

    with aba2:
        if not df_danos.empty:
            st.markdown("### 📊 Análise de Danos: Top Motoristas e Filial")
            fig_m = plot_top_motoristas(df_danos, 'Blues')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            st.write("---")
            fig_f = plot_comparativo_filial(df_danos, 'Blues')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
            
            # ==========================================
            # NOVO GRÁFICO DE CATEGORIAS - SÓ DANOS
            # ==========================================
            st.write("---")
            st.markdown("### 🏷️ Categorias com Mais Danos")
            if 'Categoria' in df_danos.columns:
                cat_danos = df_danos.groupby('Categoria')['Quantidade'].sum().nlargest(10).reset_index()
                fig_cat2 = px.bar(cat_danos, x='Quantidade', y='Categoria', orientation='h', 
                                  color='Quantidade', color_continuous_scale='Blues', text_auto='.0f')
                fig_cat2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_cat2, use_container_width=True)
        
        st.markdown("### 📋 Tabela Organizada - Danos")
        if not df_danos.empty:
            df_tabela_formatada = organizar_tabela(df_danos)
            colunas_exibicao = [c for c in ["Motorista", "Filial", "Quantidade", "descricao_ocorrencia", "Cliente", "Pedido", "Tipo_Ocorrencia"] if c in df_tabela_formatada.columns]
            df_exibicao = df_tabela_formatada[colunas_exibicao + [c for c in df_tabela_formatada.columns if c not in colunas_exibicao]]
            st.dataframe(df_exibicao, use_container_width=True)
        else:
            st.info("Nenhum dado de dano encontrado para os filtros atuais.")
            
        # Exportar Aba 2
        st.write("---")
        top_danos = df_danos.groupby('Motorista')['Quantidade'].sum().nlargest(15).reset_index() if not df_danos.empty else None
        resumo_2 = [f"Ocorrencias Exclusivas de Dano: {len(df_danos)} registros vinculados."]
        pdf_aba2 = gerar_pdf_dinamico("Relatorio - Somente Danos", resumo_2, top_danos)
        st.download_button("📄 Baixar Relatório: Danos (PDF)", data=pdf_aba2, file_name="Relatorio_Danos.pdf", mime="application/pdf", key="pdf_aba2")

    with aba3:
        if not df_faltas.empty:
            # 1. CÁLCULO DE VOLUMES
            total_itens_falta = df_faltas['Quantidade'].sum()
            total_ocorrencias_falta = len(df_faltas)
            
            c1, c2 = st.columns(2)
            c1.metric("📦 Volume de Itens Faltantes", f"{total_itens_falta:,.0f}", "Soma de Itens")
            c2.metric("📝 Total de Registros (NC)", total_ocorrencias_falta, "Linhas na Base", delta_color="off")
            
            st.write("---")

            # 2. GRÁFICO MOTORISTAS COM HOVER DA FILIAL
            st.markdown("### 📊 Top 10 Motoristas (Volume de Itens Faltantes)")
            
            # Agrupamento para o ranking
            df_mot_falta = df_faltas.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
            
            # Mapeamento da Filial (pega a filial mais frequente de cada motorista para exibir no hover)
            filial_map = df_faltas.groupby("Motorista")["Filial"].agg(
                lambda x: x.value_counts().index[0] if not x.empty else "Não Identificado"
            ).to_dict()
            df_mot_falta["Filial"] = df_mot_falta["Motorista"].map(filial_map)
            
            # Construção do gráfico com hover_data
            fig_m = px.bar(
                df_mot_falta, 
                x='Quantidade', 
                y='Motorista', 
                orientation='h',
                color='Quantidade', 
                color_continuous_scale='Reds', 
                text_auto='.0f',
                hover_data=['Filial']  # <--- Aqui a Filial volta a aparecer no mouse
            )
            fig_m.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_m, use_container_width=True)
            
            st.write("---")

            # 3. GRÁFICO FILIAL (Volume Total)
            st.markdown("### 🏢 Volume de Faltas por Filial")
            df_fil_falta = df_faltas.groupby('Filial')['Quantidade'].sum().sort_values(ascending=False).reset_index()
            fig_f = px.bar(df_fil_falta, x='Filial', y='Quantidade',
                           color='Quantidade', color_continuous_scale='Reds', text_auto='.0f')
            st.plotly_chart(fig_f, use_container_width=True)
            
            st.write("---")

            # 4. GRÁFICO CATEGORIAS
            st.markdown("### 🏷️ Categorias com Maior Perda Física")
            if 'Categoria' in df_faltas.columns:
                cat_faltas = df_faltas.groupby('Categoria')['Quantidade'].sum().nlargest(10).reset_index()
                fig_cat3 = px.bar(cat_faltas, x='Quantidade', y='Categoria', orientation='h', 
                                  color='Quantidade', color_continuous_scale='Reds', text_auto='.0f')
                fig_cat3.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_cat3, use_container_width=True)
        
        # TABELA E EXPORTAÇÃO
        st.markdown("### 📋 Tabela Organizada - Faltas")
        if not df_faltas.empty:
            df_tabela_formatada = organizar_tabela(df_faltas)
            colunas_exibicao = [c for c in ["Motorista", "Filial", "Quantidade", "descricao_ocorrencia", "Cliente", "Pedido", "Tipo_Ocorrencia"] if c in df_tabela_formatada.columns]
            df_exibicao = df_tabela_formatada[colunas_exibicao + [c for c in df_tabela_formatada.columns if c not in colunas_exibicao]]
            st.dataframe(df_exibicao, use_container_width=True)
        else:
            st.info("Nenhum dado de falta encontrado.")
    with aba4:
        st.subheader("🎯 Classificação ABC por Motorista (Reativa)")
        fig_abc, df_abc = plot_curva_abc(df_uni)
        if fig_abc:
            st.plotly_chart(fig_abc, use_container_width=True)
            st.dataframe(df_abc, use_container_width=True)
        else: st.info("Aguardando dados filtrados para calcular a Curva ABC.")
        
        # Exportar Aba 4
        st.write("---")
        resumo_4 = ["Classificacao de ofensores pelo metodo ABC (Filtro aplicado na lateral)."]
        pdf_aba4 = gerar_pdf_dinamico("Relatorio - Curva ABC", resumo_4, df_abc)
        st.download_button("📄 Baixar Relatório: Curva ABC (PDF)", data=pdf_aba4, file_name="Curva_ABC.pdf", mime="application/pdf", key="pdf_aba4")

    with aba5:
        st.subheader("🔄 Histórico Mensal de Ofensores (Motoristas)")
        fig_heat_m, df_recor_m = plot_heatmap_recorrencia(df_uni, 'Motorista')
        if fig_heat_m:
            st.plotly_chart(fig_heat_m, use_container_width=True)
            st.markdown("**📋 Motoristas Reincidentes:**")
            st.dataframe(df_recor_m, use_container_width=True)
        else: st.info("Ajuste os filtros para visualizar a recorrência.")
        
        # Exportar Aba 5
        st.write("---")
        resumo_5 = ["Acompanhamento dos Motoristas com maior reincidencia nos ultimos meses."]
        pdf_aba5 = gerar_pdf_dinamico("Recorrencia - Motoristas", resumo_5, df_recor_m)
        st.download_button("📄 Baixar Relatório: Recor. Motorista (PDF)", data=pdf_aba5, file_name="Recorrencia_Motoristas.pdf", mime="application/pdf", key="pdf_aba5")

    with aba6:
        st.subheader("🔄 Histórico Mensal de Clientes Reincidentes")
        fig_heat_c, df_recor_c = plot_heatmap_recorrencia(df_uni, 'Cliente') # Corrigido captura do df
        if fig_heat_c: st.plotly_chart(fig_heat_c, use_container_width=True)
        else: st.info("Nenhum cliente válido para análise na seleção atual.")
        
        # Exportar Aba 6
        st.write("---")
        resumo_6 = ["Acompanhamento dos Clientes com maior volume de ocorrencias reincidentes."]
        pdf_aba6 = gerar_pdf_dinamico("Recorrencia - Clientes", resumo_6, df_recor_c if fig_heat_c else None)
        st.download_button("📄 Baixar Relatório: Recor. Cliente (PDF)", data=pdf_aba6, file_name="Recorrencia_Clientes.pdf", mime="application/pdf", key="pdf_aba6")

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
        
        # Exportar Aba 7
        st.write("---")
        resumo_7 = ["Volume de itens perdidos/danificados por rota de entrega."]
        pdf_aba7 = gerar_pdf_dinamico("Rotas Logisticas Ofensoras", resumo_7, df_tab_rotas)
        st.download_button("📄 Baixar Relatório: Rotas (PDF)", data=pdf_aba7, file_name="Relatorio_Rotas.pdf", mime="application/pdf", key="pdf_aba7")

    with aba8:
        st.subheader("📝 Controle de Tratativas")
        
        @st.cache_data(ttl=600)
        def carregar_excel_nuvem_turbinado(url, aba):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status() 
            return pd.read_excel(BytesIO(response.content), sheet_name=aba, engine='openpyxl')

        # LINK CONSOLIDADO APLICADO AQUI
        link_consolidado = "https://diaslog-my.sharepoint.com/:x:/g/personal/icaro_nascimento_mmdeliverytransportes_com_br/IQALQ2WpQNljRZ827JNvOmDFAalwXuw9FECFhyM3FuOozoE?download=1"

        # --- SESSÃO 1: TRATATIVAS DE DANOS ---
        st.markdown("### 📦 Tratativas - Danos")
        df_exibicao_danos = None
        
        try:
            with st.spinner("Sincronizando Danos com o OneDrive..."):
                # Busca aba "danos"
                df_tratativas_danos = carregar_excel_nuvem_turbinado(link_consolidado, "danos").dropna(how='all').head(5).reset_index(drop=True)
            st.success("✅ Tratativas de Danos conectadas com sucesso!")
            
            with st.expander("⚙️ Escolher colunas para exibir (Danos)"):
                todas_colunas_danos = df_tratativas_danos.columns.tolist()
                colunas_selecionadas_danos = st.multiselect(
                    "Selecione as colunas desejadas:",
                    options=todas_colunas_danos,
                    default=todas_colunas_danos,
                    key="multi_danos"
                )
            
            df_exibicao_danos = df_tratativas_danos[colunas_selecionadas_danos]
            st.dataframe(df_exibicao_danos, use_container_width=True)
            
        except Exception as e:
            st.warning("⏳ Falha ao carregar a nuvem. Aguardando a verificação do link público.")
            st.info(f"Detalhe técnico: {e}")

        st.write("---") 

        # --- SESSÃO 2: TRATATIVAS DE FALTAS ---
        st.markdown("### 🛍️ Tratativas - Faltas")
        df_exibicao_faltas = None
        
        try:
            with st.spinner("Sincronizando Faltas com o OneDrive..."):
                # Busca aba "faltas"
                df_tratativas_faltas = carregar_excel_nuvem_turbinado(link_consolidado, "faltas").dropna(how='all').head(5).reset_index(drop=True)
            st.success("✅ Tratativas de Faltas conectadas direto da nuvem!")
            
            with st.expander("⚙️ Escolher colunas para exibir (Faltas)"):
                todas_colunas_faltas = df_tratativas_faltas.columns.tolist()
                colunas_selecionadas_faltas = st.multiselect(
                    "Selecione as colunas desejadas:",
                    options=todas_colunas_faltas,
                    default=todas_colunas_faltas,
                    key="multi_faltas"
                )
                
            df_exibicao_faltas = df_tratativas_faltas[colunas_selecionadas_faltas]
            st.dataframe(df_exibicao_faltas, use_container_width=True)
            
        except Exception as e:
            st.error("⚠️ Erro ao conectar com a sua planilha na nuvem.")
            st.info(f"Detalhe técnico: {e}")
            
        # --- EXPORTAR ABA 8 ---
        st.write("---")
        resumo_8 = ["Extracao rapida do controle online de tratativas e ressarcimentos."]
        
        # Envia para o PDF a tabela já com as colunas filtradas pelo usuário
        df_pdf_8 = df_exibicao_danos if df_exibicao_danos is not None else df_exibicao_faltas
        
        pdf_aba8 = gerar_pdf_dinamico("Controle de Tratativas (Nuvem)", resumo_8, df_pdf_8)
        st.download_button(
            label="📄 Baixar Relatório: Tratativas (PDF)", 
            data=pdf_aba8, 
            file_name="Controle_Tratativas.pdf", 
            mime="application/pdf", 
            key="pdf_aba8"
        )
    with aba9:
        st.subheader("🚨 Dossiê de Fraudes")
        alertas = pd.DataFrame()
        if not df_uni.empty:
            df_cli = df_uni[~df_uni['Cliente'].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
            f_vol = df_cli[df_cli['Quantidade'] >= 900].copy()
            f_vol['Motivo'] = 'Volume Crítico'
            
            df_rep = df_cli[df_cli['Quantidade'] >= 10].copy()
            cli_susp = df_rep.groupby(['Cliente', 'Quantidade']).size().reset_index(name='V')
            cli_susp = cli_susp[cli_susp['V'] > 1]
            f_rep = pd.merge(df_cli, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'])
            f_rep['Motivo'] = 'Reclamação Idêntica'
            
            mot_suspeitos = df_cli.groupby('Motorista')['Cliente'].nunique().reset_index(name='Qtd_Clientes')
            lista_mot = mot_suspeitos[mot_suspeitos['Qtd_Clientes'] > 50]['Motorista']
            f_mot = df_cli[df_cli['Motorista'].isin(lista_mot)].copy()
            f_mot['Motivo'] = 'Motorista Risco: +50 Clientes Afetados'
            
            alertas = pd.concat([f_vol, f_rep, f_mot])
            if not alertas.empty:
                alertas = alertas.drop_duplicates(subset=['Pedido', 'Motivo'])
                alertas = alertas.loc[:, ~alertas.columns.duplicated()] 
                st.error(f"⚠️ {len(alertas)} Indícios Detectados")
                colunas_exibicao = ['Motivo', 'Cliente', 'Pedido', 'Quantidade', 'Tipo_Ocorrencia', 'Motorista', 'Filial', 'Canal']
                df_exibicao = alertas[colunas_exibicao].copy()
                st.dataframe(df_exibicao, use_container_width=True)
            else: st.success("✅ Tudo limpo no filtro atual.")
                
        # Exportar Aba 9
        st.write("---")
        resumo_9 = [f"Total de alertas do sistema: {len(alertas)} anomalias."]
        pdf_aba9 = gerar_pdf_dinamico("Dossie de Fraude e Alertas", resumo_9, alertas)
        st.download_button("📄 Baixar Relatório: Fraudes (PDF)", data=pdf_aba9, file_name="Dossie_Fraudes.pdf", mime="application/pdf", key="pdf_aba9")

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

except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.code(traceback.format_exc())
  
    with aba11:
        st.subheader("📈 Análise de Tendências Temporais")
        
        # 1. Filtro para o usuário escolher qual planilha (base) ele quer ver
        tipo_base = st.radio(
            "Qual base de dados você quer analisar na linha do tempo?", 
            ["Ambas (Geral)", "Somente Danos", "Somente Faltas"], 
            horizontal=True
        )
        
        # 2. Filtro para escolher se a visão é por Mês ou por Semana
        tipo_visao = st.radio(
            "Selecione a periodicidade:", 
            ["Mensal", "Semanal"], 
            horizontal=True
        )
        param_tempo = 'M' if tipo_visao == "Mensal" else 'W'
        
        # 3. Direciona os dados corretos dependendo da escolha do usuário
        if tipo_base == "Somente Danos":
            df_plot = df_danos  
        elif tipo_base == "Somente Faltas":
            df_plot = df_faltas 
        else:
            df_plot = df_uni    
            
        # 4. Gera o gráfico se a base não estiver vazia
        if not df_plot.empty:
            fig_tempo = plot_evolucao_temporal(df_plot, periodicidade=param_tempo)
            if fig_tempo:
                st.plotly_chart(fig_tempo, use_container_width=True)
            else:
                st.warning("Não foi possível gerar o gráfico de linha do tempo com as datas atuais.")
        else:
            st.warning(f"Não há dados disponíveis para a seleção: {tipo_base}")
        
        st.divider()
        
  
# O except fica totalmente colado no canto esquerdo, NO FINAL DE TUDO!
except Exception as e:
    st.error(f"Erro no processamento: {e}")
    st.code(traceback.format_exc())
