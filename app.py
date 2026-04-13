import streamlit as st
import pandas as pd

def aplicar_filtros_barra_lateral(df_uni_base, df_danos_base, df_faltas_base):
    """Cria a barra lateral, captura as escolhas do usuário e filtra os DataFrames."""
    
    with st.sidebar:
        # --- BOTÃO LIMPAR (No topo para UX rápida) ---
        if st.button("🔄 Limpar Todos os Filtros", use_container_width=True):
            # Limpa o estado da sessão para garantir que as caixas voltem a ficar vazias
            st.session_state.clear()
            st.rerun()
            
        st.header("🔍 Filtros Integrados")
        st.divider()
        
        # --- CATEGORIA: INTELIGÊNCIA ANALÍTICA ---
        st.subheader("📈 Inteligência Analítica")
        if not df_uni_base.empty:
            percentil = st.slider(
                "Cortar Outliers (Percentil):", 
                min_value=90, max_value=100, value=100,
                help="100 mantém tudo. 99 remove o 1% das ocorrências com volumes absurdamente altos que podem distorcer o gráfico."
            )
            # O cálculo mágico do percentil
            limite_qtde = df_uni_base["Quantidade"].quantile(percentil / 100)
            st.caption(f"💡 Limite de corte atual: até **{int(limite_qtde)} itens** por ocorrência.")
        else:
            limite_qtde = 1000
            
        st.divider()
        
        # --- CATEGORIA: TEMPO ---
        st.subheader("📅 Tempo")
        if not df_uni_base.empty and 'Data_Filtro' in df_uni_base.columns and not df_uni_base['Data_Filtro'].dropna().empty:
            min_date = df_uni_base['Data_Filtro'].dropna().min().date()
            max_date = df_uni_base['Data_Filtro'].dropna().max().date()
            if min_date == max_date:
                min_date = min_date - pd.Timedelta(days=7)
        else:
            hoje = pd.to_datetime('today').date()
            min_date = hoje - pd.Timedelta(days=30)
            max_date = hoje

        datas_selecionadas = st.date_input(
            "Período de Análise:",
            value=(min_date, max_date),
            format="DD/MM/YYYY",
            help="Selecione primeiro a data de INÍCIO e depois a data de FIM."
        )
        
        st.divider()

        # ==========================================
        # PREPARAÇÃO DA CASCATA DE OPÇÕES
        # Usamos uma cópia da base unificada apenas para alimentar os menus de forma inteligente
        # ==========================================
        df_opcoes = df_uni_base.copy()

        # --- CATEGORIA: OPERACIONAL ---
        st.subheader("🏢 Operacional")
        
        # 1. Filial
        opcoes_filial = sorted(df_opcoes["Filial"].dropna().unique())
        # O parâmetro 'key' é essencial para que o botão de "Limpar Filtros" funcione nesta caixa
        filial_sel = st.selectbox("Filial:", options=opcoes_filial, index=None, placeholder="Todas as Filiais", key="f_filial")

        # EFEITO CASCATA: Se escolheu filial, restringe a base de opções para os próximos menus
        if filial_sel:
            df_opcoes = df_opcoes[df_opcoes["Filial"] == filial_sel]

        # 2. Motorista (A lista já sofre o efeito da Filial acima)
        opcoes_motorista = sorted(df_opcoes["Motorista"].dropna().unique())
        motorista_sel = st.selectbox("Motorista:", options=opcoes_motorista, index=None, placeholder="Todos os Motoristas", key="f_motorista")

        # EFEITO CASCATA: Se escolheu motorista, restringe a base para empresa/canal
        if motorista_sel:
            df_opcoes = df_opcoes[df_opcoes["Motorista"] == motorista_sel]

        st.divider()

        # --- CATEGORIA: COMERCIAL ---
        st.subheader("📦 Comercial")
        
        # 3. Empresa (A lista já reflete o motorista e a filial selecionados)
        opcoes_empresa = sorted([str(x) for x in df_opcoes["Empresa"].dropna().unique() if str(x) not in ['Não Identificado', 'N/A']])
        empresa_sel = st.selectbox("Empresa (Danos):", options=opcoes_empresa, index=None, placeholder="Todas as Empresas", key="f_empresa")

        # EFEITO CASCATA FINAL
        if empresa_sel:
            df_opcoes = df_opcoes[df_opcoes["Empresa"] == empresa_sel]

        # 4. Canal
        opcoes_canal = sorted([str(x) for x in df_opcoes["Canal"].dropna().unique() if str(x) not in ['Não Identificado', 'N/A']])
        canal_sel = st.multiselect("Marca/Canal (Faltas):", options=opcoes_canal, placeholder="Escolha um ou mais...", key="f_canal")

    # ==========================================
    # APLICANDO AS REGRAS MATEMÁTICAS (BLINDADAS)
    # ==========================================
    
    # GARANTIA FINAL: Força a conversão das bases na hora do recorte para evitar bugs de tipo
    if 'Data_Filtro' in df_uni_base.columns: df_uni_base["Data_Filtro"] = pd.to_datetime(df_uni_base["Data_Filtro"], errors='coerce')
    if 'Data_Filtro' in df_danos_base.columns: df_danos_base["Data_Filtro"] = pd.to_datetime(df_danos_base["Data_Filtro"], errors='coerce')
    if 'Data_Filtro' in df_faltas_base.columns: df_faltas_base["Data_Filtro"] = pd.to_datetime(df_faltas_base["Data_Filtro"], errors='coerce')

    # 1. Aplica o novo limite seguro do Percentil
    df_uni = df_uni_base[df_uni_base["Quantidade"] <= limite_qtde].copy()
    df_danos = df_danos_base[df_danos_base["Quantidade"] <= limite_qtde].copy()
    df_faltas = df_faltas_base[df_faltas_base["Quantidade"] <= limite_qtde].copy()

    # 2. Aplica o filtro de data somente se o utilizador clicou no INÍCIO e FIM
    if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2:
        start_date, end_date = datas_selecionadas
        t_start = pd.to_datetime(start_date)
        t_end = pd.to_datetime(end_date) + pd.Timedelta(hours=23, minutes=59, seconds=59)
        
        if 'Data_Filtro' in df_uni.columns: 
            df_uni = df_uni[(df_uni['Data_Filtro'] >= t_start) & (df_uni['Data_Filtro'] <= t_end)]
        if 'Data_Filtro' in df_danos.columns: 
            df_danos = df_danos[(df_danos['Data_Filtro'] >= t_start) & (df_danos['Data_Filtro'] <= t_end)]
        if 'Data_Filtro' in df_faltas.columns: 
            df_faltas = df_faltas[(df_faltas['Data_Filtro'] >= t_start) & (df_faltas['Data_Filtro'] <= t_end)]

    # 3. Demais Filtros...
    if motorista_sel is not None:
        df_uni = df_uni[df_uni["Motorista"] == motorista_sel]
        df_danos = df_danos[df_danos["Motorista"] == motorista_sel]
        df_faltas = df_faltas[df_faltas["Motorista"] == motorista_sel]
        
    if filial_sel is not None:
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
            
    if empresa_sel is not None:
        df_uni = df_uni[df_uni["Empresa"] == empresa_sel]
        df_danos = df_danos[df_danos["Empresa"] == empresa_sel]
        df_faltas = df_faltas[df_faltas["Empresa"] == empresa_sel]
        
    if len(canal_sel) > 0:
        df_uni = df_uni[df_uni["Canal"].isin(canal_sel)]
        df_danos = df_danos[df_danos["Canal"].isin(canal_sel)]
        df_faltas = df_faltas[df_faltas["Canal"].isin(canal_sel)]

    return df_uni, df_danos, df_faltas
