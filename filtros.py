import streamlit as st

def aplicar_filtros_barra_lateral(df_uni_base, df_danos_base, df_faltas_base):
    """Cria a barra lateral, captura as escolhas do usuário e filtra os DataFrames."""
    
    with st.sidebar:
        st.header("🔍 Filtros Integrados")
        
        max_itens = int(df_uni_base["Quantidade"].max()) if not df_uni_base.empty else 1000
        outlier_limite = st.slider("🚫 Ocultar registos acima de (Outliers):", 1, max_itens, max_itens)
        st.divider()
        
        ordem_exibicao = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        meses_na_base = [m for m in ordem_exibicao if m in df_uni_base["Periodo"].unique()]
        periodo_sel = st.selectbox("📅 Escolha o Mês:", ["Todos"] + meses_na_base)
        
        filial_sel = st.selectbox("🏢 Filial:", ["Todas"] + sorted(df_uni_base["Filial"].unique().tolist()))
        motorista_sel = st.selectbox("🚛 Motorista:", ["Todos"] + sorted(df_uni_base["Motorista"].unique().tolist()))
        
        opcoes_empresa = [str(x) for x in df_uni_base["Empresa"].unique() if str(x) not in ['Não Identificado', 'N/A']]
        empresa_sel = st.selectbox("🏭 Empresa (Danos):", ["Todas"] + sorted(opcoes_empresa))
        
        opcoes_canal = [str(x) for x in df_uni_base["Canal"].unique() if str(x) not in ['Não Identificado', 'N/A']]
        canal_sel = st.multiselect("🛍️ Marca Canal (Faltas) [Vazio = Todos]:", sorted(opcoes_canal))

    # --- Aplicando as regras ---
    df_uni = df_uni_base[df_uni_base["Quantidade"] <= outlier_limite].copy()
    df_danos = df_danos_base[df_danos_base["Quantidade"] <= outlier_limite].copy()
    df_faltas = df_faltas_base[df_faltas_base["Quantidade"] <= outlier_limite].copy()

    if periodo_sel != "Todos":
        df_uni = df_uni[df_uni["Periodo"] == periodo_sel]
        df_danos = df_danos[df_danos["Periodo"] == periodo_sel]
        df_faltas = df_faltas[df_faltas["Periodo"] == periodo_sel]
    if motorista_sel != "Todos":
        df_uni = df_uni[df_uni["Motorista"] == motorista_sel]
        df_danos = df_danos[df_danos["Motorista"] == motorista_sel]
        df_faltas = df_faltas[df_faltas["Motorista"] == motorista_sel]
    if filial_sel != "Todas":
        df_uni = df_uni[df_uni["Filial"] == filial_sel]
        df_danos = df_danos[df_danos["Filial"] == filial_sel]
        df_faltas = df_faltas[df_faltas["Filial"] == filial_sel]
    if empresa_sel != "Todas":
        df_uni = df_uni[df_uni["Empresa"] == empresa_sel]
        df_danos = df_danos[df_danos["Empresa"] == empresa_sel]
        df_faltas = df_faltas[df_faltas["Empresa"] == empresa_sel]
    if len(canal_sel) > 0:
        df_uni = df_uni[df_uni["Canal"].isin(canal_sel)]
        df_danos = df_danos[df_danos["Canal"].isin(canal_sel)]
        df_faltas = df_faltas[df_faltas["Canal"].isin(canal_sel)]

    return df_uni, df_danos, df_faltas