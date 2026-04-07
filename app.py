import streamlit as st
import pandas as pd
import plotly.express as px   # <--- É ESSA LINHA AQUI QUE FALTOU!
import plotly.graph_objects as go
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
        # --- CALCULANDO AS TAXAS DO SEU AMIGO ---
        total_ocorrencias = len(df_uni)
        
        # Evita erro de divisão por zero caso o filtro deixe a base vazia
        if total_ocorrencias > 0:
            taxa_dano = len(df_danos) / total_ocorrencias
            taxa_falta = len(df_faltas) / total_ocorrencias
            media_itens_por_ocorrencia = df_uni["Quantidade"].sum() / total_ocorrencias
        else:
            taxa_dano = 0
            taxa_falta = 0
            media_itens_por_ocorrencia = 0

        # --- EXIBINDO AS MÉTRICAS COM AS PORCENTAGENS ---
        c1, c2, c3, c4 = st.columns(4)
        
        # O st.metric aceita um valor principal e uma "informação extra" menor embaixo
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

  # --- NOVO: A SANFONA DE INVESTIGAÇÃO (DRILL DOWN) ---
        st.write("---")
        with st.expander("🔎 Ferramenta de Investigação: Explorar Dados Detalhados (Drill Down)"):
            st.markdown("Use os filtros na barra lateral esquerda para isolar um Motorista ou Filial e veja o detalhamento nota a nota abaixo.")
            
            if not df_uni.empty:
                # Usa a nossa função já existente para deixar a tabela bonita
                st.dataframe(organizar_tabela(df_uni), use_container_width=True)
            else:
                st.info("Nenhum dado encontrado para os filtros atuais.")
    with aba2:
        if not df_danos.empty:
            st.markdown("### 📊 Análise de Danos: Top Motoristas e Filial")
            fig_m = plot_top_motoristas(df_danos, 'Blues')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            
            st.write("---")
            
            fig_f = plot_comparativo_filial(df_danos, 'Blues')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
        
        st.markdown("### 📋 Tabela Organizada - Danos")
        
        if not df_danos.empty:
            # 1. Pega o dataframe já formatado pela sua função original
            df_tabela_formatada = organizar_tabela(df_danos)
            
            # 2. Aplica a ordem operacional solicitada
            ordem_colunas = [
                "Motorista", 
                "Filial", 
                "Quantidade", 
                "descricao_ocorrencia", 
                "Cliente", 
                "Pedido", 
                "Tipo_Ocorrencia"
          
            ]
            
           
        with aba3:
        if not df_faltas.empty:
            st.markdown("### 📊 Análise de Faltas: Top Motoristas e Filial")
            # Usa 'Reds' para diferenciar visualmente a aba de faltas (ou mude para 'Blues' se preferir manter igual)
            fig_m = plot_top_motoristas(df_faltas, 'Reds')
            if fig_m: st.plotly_chart(fig_m, use_container_width=True)
            
            st.write("---")
            
            fig_f = plot_comparativo_filial(df_faltas, 'Reds')
            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
        
        st.markdown("### 📋 Tabela Organizada - Faltas")
        
        if not df_faltas.empty:
            # 1. Pega o dataframe já formatado pela sua função original
            df_tabela_formatada = organizar_tabela(df_faltas)
            
            # 2. Aplica a ordem operacional solicitada
            ordem_colunas = [
                "Motorista", 
                "Filial", 
                "Quantidade", 
                "descricao_ocorrencia", 
                "Cliente", 
                "Pedido", 
                "Tipo_Ocorrencia"
            ]
            
            # 3. Garante que as colunas existam (evita quebra do código) e joga o resto pro final
            colunas_exibicao = [col for col in ordem_colunas if col in df_tabela_formatada.columns]
            colunas_restantes = [col for col in df_tabela_formatada.columns if col not in colunas_exibicao]
            colunas_finais = colunas_exibicao + colunas_restantes
            
            # 4. Exibe a tabela redondinha na tela
            st.dataframe(df_tabela_formatada[colunas_finais], use_container_width=True)
        else:
            st.info("Nenhum dado de falta encontrado para os filtros atuais.")
            
        

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
        st.subheader("📝 Controle de Tratativas (Conexão Nuvem ☁️)")
        
        # 1. COLE SEU LINK AQUI (Lembre-se do ?download=1 no final)
        link_excel_nuvem = "https://diaslog-my.sharepoint.com/:x:/g/personal/arthur_rodrigues_mddelivery_com_br/IQDpm8MBmO03R5YbkXJrr12XAYpkbZyJ7mmYll2J7jvrdO8?download=1"
        
        # 2. COLOQUE O NOME EXATO DA ABA QUE VOCÊ QUER LER
        nome_da_aba = "TOP5DANO"
        
        # Usamos o cache_data para ele não ficar baixando o Excel toda vez que você clicar num filtro
        @st.cache_data(ttl=600) # O cache dura 10 minutos (600 segundos)
        def carregar_excel_nuvem(url, aba):
            # O parâmetro sheet_name é o que garante que ele só leia a aba certa!
            df_nuvem = pd.read_excel(url, sheet_name=aba, engine='openpyxl')
            return df_nuvem

        try:
            # Mostra um ícone de carregamento enquanto o Python vai até a Microsoft buscar os dados
            with st.spinner("Sincronizando com o Microsoft Cloud..."):
                df_tratativas_nuvem = carregar_excel_nuvem(link_excel_nuvem, nome_da_aba)
            
            st.success("✅ Conectado ao Excel Online com sucesso!")
            
            # Mostra a tabela na tela
            st.dataframe(df_tratativas_nuvem, use_container_width=True)
            
        except Exception as e:
            st.error("⚠️ Erro ao conectar com a nuvem.")
            st.markdown("Verifique se o link está correto (terminando em `?download=1`), se o nome da aba está exato e se a planilha tem permissão de leitura.")
            st.info(f"Detalhe técnico do erro para o desenvolvedor: {e}")

    with aba9:
        st.subheader("🚨 Dossiê de Fraudes")
        if not df_uni.empty:
            df_cli = df_uni[~df_uni['Cliente'].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
            
            # Regra 1: Volume Crítico (Ocorrência com mais de 900 itens de uma vez)
            f_vol = df_cli[df_cli['Quantidade'] >= 900].copy()
            f_vol['Motivo'] = 'Volume Crítico'
            
            # Regra 2: Reclamação Idêntica (Mesmo cliente, mesma quantidade, repetidas vezes)
            df_rep = df_cli[df_cli['Quantidade'] >= 10].copy()
            cli_susp = df_rep.groupby(['Cliente', 'Quantidade']).size().reset_index(name='V')
            cli_susp = cli_susp[cli_susp['V'] > 1]
            f_rep = pd.merge(df_cli, cli_susp[['Cliente', 'Quantidade']], on=['Cliente', 'Quantidade'])
            f_rep['Motivo'] = 'Reclamação Idêntica'
            
            # --- NOVA Regra 3: Motorista Suspeito (Pulverização em + de 50 clientes diferentes) ---
            mot_suspeitos = df_cli.groupby('Motorista')['Cliente'].nunique().reset_index(name='Qtd_Clientes')
            lista_mot = mot_suspeitos[mot_suspeitos['Qtd_Clientes'] > 50]['Motorista']
            
            f_mot = df_cli[df_cli['Motorista'].isin(lista_mot)].copy()
            f_mot['Motivo'] = 'Motorista Risco: +50 Clientes Afetados'
            # -------------------------------------------------------------------------------------
            
            # Junta todas as regras
            alertas = pd.concat([f_vol, f_rep, f_mot])
            
            if not alertas.empty:
                # Remove duplicidades caso a mesma ocorrência caia em mais de uma regra
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
