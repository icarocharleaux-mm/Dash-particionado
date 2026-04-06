import streamlit as st

def aplicar_filtros_barra_lateral(df_uni_base, df_danos_base, df_faltas_base):
    """Cria a barra lateral, captura as escolhas do usuário e filtra os DataFrames."""
    
    with st.sidebar:
        st.header("🔍 Filtros Integrados")
        
        max_itens = int(df_uni_base["Quantidade"].max()) if not df_uni_base.empty else 1000
        outlier_limite = st.slider("🚫 Ocultar registos acima de (Outliers):", 1, max_itens, max_itens)
        st.divider()
        
        # --- 1. Preparando as listas limpas (com dropna) ---
        ordem_exibicao = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        meses_na_base = [m for m in ordem_exibicao if m in df_uni_base["Periodo"].dropna().unique()]
        
        opcoes_filial = sorted(df_uni_base["Filial"].dropna().unique())
        opcoes_motorista = sorted(df_uni_base["Motorista"].dropna().unique())
        
        opcoes_empresa = sorted([str(x) for x in df_uni_base["Empresa"].dropna().unique() if str(x) not in ['Não Identificado', 'N/A']])
        opcoes_canal = sorted([str(x) for x in df_uni_base["Canal"].dropna().unique() if str(x) not in ['Não Identificado', 'N/A']])

        # --- 2. Criando as caixas de seleção com index=None ---
        # O Mês mantemos com o padrão "Todos" pois já usa a sua lógica visual de calendário
        periodo_sel = st.selectbox("📅 Escolha o Mês:", ["Todos"] + meses_na_base)
        
        # Os outros ganham o botão de limpar e a busca automática
        filial_sel = st.selectbox("🏢 Filial:", options=opcoes_filial, index=None, placeholder="Todas")
        motorista_sel = st.selectbox("🚛 Motorista:", options=opcoes_motorista, index=None, placeholder="Todos")
        empresa_sel = st.selectbox("🏭 Empresa (Danos):", options=opcoes_empresa, index=None, placeholder="Todas")
        canal_sel = st.multiselect("🛍️ Marca Canal (Faltas):", options=opcoes_canal, placeholder="Escolha um ou mais...")

    # --- 3. Aplicando as regras matemáticas ---
    df_uni = df_uni_base[df_uni_base["Quantidade"] <= outlier_limite].copy()
    df_danos = df_danos_base[df_danos_base["Quantidade"] <= outlier_limite].copy()
    df_faltas = df_faltas_base[df_faltas_base["Quantidade"] <= outlier_limite].copy()

    if periodo_sel != "Todos":
        df_uni = df_uni[df_uni["Periodo"] == periodo_sel]
        df_danos = df_danos[df_danos["Periodo"] == periodo_sel]
        df_faltas = df_faltas[df_faltas["Periodo"] == periodo_sel]

    # Mudou de '!= "Todos"' para 'is not None'
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
