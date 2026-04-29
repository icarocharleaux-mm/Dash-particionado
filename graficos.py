import plotly.express as px
import pandas as pd
import streamlit as st

def plot_top_motoristas(df_filtrado, escala_cor):
    if df_filtrado.empty: return None
    ranking = df_filtrado.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
    filial_map = df_filtrado.groupby("Motorista")["Filial"].agg(lambda x: x.value_counts().index[0] if not x.empty else "N/A").to_dict()
    ranking["Filial"] = ranking["Motorista"].map(filial_map)
    fig = px.bar(ranking, x='Quantidade', y='Motorista', orientation='h', color='Quantidade', color_continuous_scale=escala_cor, hover_data=['Filial'])
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    return fig

def plot_comparativo_filial(df_filtrado, escala_cor):
    if df_filtrado.empty: return None
    contagem = df_filtrado.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
    fig = px.bar(contagem, x='Filial', y='Quantidade', text='Quantidade', color='Quantidade', color_continuous_scale=escala_cor)
    fig.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    return fig

def plot_pizza_tipo_ocorrencia(df_filtrado):
    if df_filtrado.empty: return None
    pizza = df_filtrado.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
    fig = px.pie(pizza, names='Tipo_Ocorrencia', values='Quantidade', hole=0.4, color_discrete_map={'Dano':'#1f77b4', 'Falta':'#d62728'})
    return fig

def plot_curva_abc(df_filtrado):
    """Calcula a Curva ABC e retorna o gráfico e a tabela final."""
    if df_filtrado.empty: return None, None
    abc = df_filtrado.groupby('Motorista')['Quantidade'].sum().sort_values(ascending=False).reset_index()
    abc['SomaAcum'] = abc['Quantidade'].cumsum()
    abc['PercAcum'] = 100 * abc['SomaAcum'] / abc['Quantidade'].sum()
    abc['Classe'] = abc['PercAcum'].apply(lambda x: 'A (Crítico - 70%)' if x <= 70 else ('B (Atenção - 20%)' if x <= 90 else 'C (Normal - 10%)'))
    fig = px.bar(abc, x='Motorista', y='Quantidade', color='Classe', color_discrete_map={'A (Crítico - 70%)':'#d62728','B (Atenção - 20%)':'#ff7f0e','C (Normal - 10%)':'#2ca02c'})
    return fig, abc

def plot_heatmap_recorrencia(df_filtrado, coluna_alvo):
    """Gera o Heatmap e a tabela de reincidentes. Funciona para Motorista ou Cliente!"""
    df_valido = df_filtrado[~df_filtrado[coluna_alvo].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', ''])].copy()
    if df_valido.empty: return None, None
    
    df_hist = df_valido.groupby([coluna_alvo, 'Periodo']).size().reset_index(name='Casos')
    df_pivot = df_hist.pivot_table(index=coluna_alvo, columns='Periodo', values='Casos', fill_value=0)
    
    meses_ref = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    colunas_existentes = [m for m in meses_ref if m in df_pivot.columns]
    df_pivot = df_pivot[colunas_existentes]
    
    df_pivot['Total'] = df_pivot.sum(axis=1)
    df_pivot_plot = df_pivot.sort_values('Total', ascending=False).drop(columns=['Total']).head(25)
    
    fig = px.imshow(df_pivot_plot, text_auto=True, aspect="auto", color_continuous_scale='YlOrRd', labels=dict(x="Mês", y=coluna_alvo, color="Ocorrências"))
    
    recor_resumo = df_valido.groupby(coluna_alvo)['Periodo'].nunique().sort_values(ascending=False).reset_index()
    recor_resumo.columns = [coluna_alvo, 'Meses com Problemas']
    return fig, recor_resumo[recor_resumo['Meses com Problemas'] > 1]

def plot_mapa_rotas(df_uni, df_mapa_agg, df_coord_agg):
    """Cruza os dados geográficos e gera o mapa interativo."""
    df_rotas = df_uni[~df_uni['Rota'].str.upper().isin(['N/A', 'NAN', 'NÃO IDENTIFICADO', ''])]
    if df_rotas.empty: return None, None
    
    tabela_r = df_rotas.groupby('Rota').size().reset_index(name='Total_Geral')
    tabela_r['Rota'] = tabela_r['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    if not df_coord_agg.empty and 'Rota' in df_coord_agg.columns:
        df_coord_agg['Rota'] = df_coord_agg['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    else: df_coord_agg = pd.DataFrame(columns=['Rota', 'LATITUDE', 'LONGITUDE'])
        
    if not df_mapa_agg.empty and 'Rota' in df_mapa_agg.columns:
        df_mapa_agg['Rota'] = df_mapa_agg['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    else: df_mapa_agg = pd.DataFrame(columns=['Rota', 'Setor', 'Bairro'])
    
    tabela_final = pd.merge(tabela_r, df_mapa_agg, on='Rota', how='left')
    tabela_final = pd.merge(tabela_final, df_coord_agg, on='Rota', how='left')
    
    df_mapa_plot = tabela_final.dropna(subset=['LATITUDE', 'LONGITUDE'])
    
    fig = None
    if not df_mapa_plot.empty:
        fig = px.scatter_mapbox(df_mapa_plot, lat="LATITUDE", lon="LONGITUDE", size="Total_Geral", color="Total_Geral", hover_name="Setor", hover_data=["Rota", "Bairro"], zoom=7, mapbox_style="carto-positron")
    
    return fig, tabela_final[['Rota', 'Setor', 'Bairro', 'Total_Geral']].sort_values('Total_Geral', ascending=False)

def plot_evolucao_temporal(df, periodicidade='M'):
    """Gera um gráfico de linha do tempo agrupando ocorrências por Filial."""
    if df.empty:
        return None
        
    df_temp = df.copy()
    
    # 💡 O PULO DO GATO: Pega automaticamente o nome da PRIMEIRA coluna (Coluna A)
    col_data = df_temp.columns[0]
    
    # Tenta converter essa Coluna A para o formato de data
    df_temp[col_data] = pd.to_datetime(df_temp[col_data], errors='coerce')
    df_temp = df_temp.dropna(subset=[col_data])
    
    if df_temp.empty:
        return None

    if periodicidade == 'M':
        df_temp['Linha_Tempo'] = df_temp[col_data].dt.to_period('M').astype(str) 
        titulo = "Evolução Mensal de Ocorrências por Filial"
    else:
        df_temp['Linha_Tempo'] = df_temp[col_data].dt.to_period('W').astype(str)
        titulo = "Evolução Semanal de Ocorrências por Filial"
        
    df_agrupado = df_temp.groupby(['Linha_Tempo', 'Filial'])['Quantidade'].sum().reset_index()
    
    # Se, por acaso, a tabela agrupada ficar vazia, não gera o gráfico
    if df_agrupado.empty:
        return None
        
    fig = px.line(
        df_agrupado, x='Linha_Tempo', y='Quantidade', color='Filial', 
        markers=True, title=titulo, color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    fig.update_layout(xaxis_title="Período", yaxis_title="Volume de Itens (Qtd)", hovermode="x unified", legend_title="Filial")
    return fig
