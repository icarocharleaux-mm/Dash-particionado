import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import logging

# ==========================================
# DEFINIÇÃO DE PALETAS PADRÃO DIAS+
# ==========================================
DIAS_TEAL_SCALE = ['#0B2E3A', '#1A5A68', '#1A8090', '#2DC5B4']
DIAS_RED_SCALE  = ['#0B2E3A', '#7a2826', '#a65452', '#C47A77']

COLOR_TEAL_MAIN = '#2DC5B4'
COLOR_RED_MAIN  = '#C47A77'
COLOR_AMBER     = '#eab308'
COLOR_WHITE_80  = 'rgba(255,255,255,0.8)'
COLOR_WHITE_50  = 'rgba(255,255,255,0.5)'

def _aplicar_layout_dark_dias(fig):
    """Função auxiliar para padronizar o visual dos gráficos com o Dark Mode Dias+"""
    fig.update_layout(
        font=dict(family="Montserrat, sans-serif", color="#ffffff"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            zerolinecolor='rgba(255,255,255,0.1)',
            tickfont=dict(color=COLOR_WHITE_80),
            titlefont=dict(color=COLOR_WHITE_80)
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            zerolinecolor='rgba(255,255,255,0.1)',
            tickfont=dict(color=COLOR_WHITE_80),
            titlefont=dict(color=COLOR_WHITE_80)
        ),
        legend=dict(
            font=dict(color=COLOR_WHITE_80),
            bgcolor='rgba(0,0,0,0.2)'
        )
    )
    return fig

def plot_top_motoristas(df_filtrado, escala_cor=DIAS_TEAL_SCALE):
    if df_filtrado.empty: return None
    ranking = df_filtrado.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
    filial_map = df_filtrado.groupby(\"Motorista\")[\"Filial\"].agg(lambda x: x.value_counts().index[0] if not x.empty else \"N/A\").to_dict()
    ranking[\"Filial\"] = ranking[\"Motorista\"].map(filial_map)
    
    fig = px.bar(ranking, x='Quantidade', y='Motorista', orientation='h', color='Quantidade', color_continuous_scale=escala_cor, hover_data=['Filial'])
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    return _aplicar_layout_dark_dias(fig)

def plot_comparativo_filial(df_filtrado, escala_cor=DIAS_TEAL_SCALE):
    if df_filtrado.empty: return None
    contagem = df_filtrado.groupby(\"Filial\")[\"Quantidade\"].sum().reset_index().sort_values(\"Quantidade\", ascending=False)
    
    fig = px.bar(contagem, x='Filial', y='Quantidade', text='Quantidade', color='Quantidade', color_continuous_scale=escala_cor)
    fig.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    fig.update_traces(textposition='outside')
    return _aplicar_layout_dark_dias(fig)

def plot_pizza_tipo_ocorrencia(df_filtrado):
    if df_filtrado.empty: return None
    resumo = df_filtrado.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
    
    # Mapeamento estrito usando Teal para OK/Danos Controlados e Vermelho para Faltas/Críticos
    mapa_cores = {'Dano': COLOR_TEAL_MAIN, 'Falta': COLOR_RED_MAIN}
    
    fig = px.pie(resumo, values='Quantidade', names='Tipo_Ocorrencia', hole=0.4,
                 color='Tipo_Ocorrencia', color_discrete_map=mapa_cores)
    return _aplicar_layout_dark_dias(fig)

def plot_curva_abc(df):
    if df.empty: return None, pd.DataFrame()
    
    df_mot = df.groupby('Motorista')['Quantidade'].sum().reset_index()
    df_mot = df_mot.sort_values(by='Quantidade', ascending=False).reset_index(drop=True)
    
    total_itens = df_mot['Quantidade'].sum()
    if total_itens == 0: return None, pd.DataFrame()
    
    df_mot['Soma_Acumulada'] = df_mot['Quantidade'].cumsum()
    df_mot['Percentual_Acumulado'] = (df_mot['Soma_Acumulada'] / total_itens) * 100
    
    def classificar_abc(p):
        if p <= 80: return 'A'
        elif p <= 95: return 'B'
        else: return 'C'
        
    df_mot['Classe'] = df_mot['Percentual_Acumulado'].apply(classificar_abc)
    
    # Cores fixas da identidade para cada classe da curva ABC
    mapa_cores_abc = {'A': COLOR_RED_MAIN, 'B': COLOR_AMBER, 'C': COLOR_TEAL_MAIN}
    
    fig = px.bar(df_mot, x='Motorista', y='Quantidade', color='Classe',
                 color_discrete_map=mapa_cores_abc,
                 title="Curva ABC de Ofensores (Itens)",
                 labels={'Quantidade': 'Qtd Itens', 'Percentual_Acumulado': '% Acumulado'})
    
    fig.add_scatter(x=df_mot['Motorista'], y=df_mot['Percentual_Acumulado'], 
                    yaxis='y2', name='% Acumulado', mode='lines+markers', 
                    line=dict(color='#ffffff', width=2))
    
    fig.update_layout(
        yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 105], gridcolor='rgba(255,255,255,0.02)'),
        xaxis={'categoryorder':'total descending'},
        legend_title_text='Classe'
    )
    return _aplicar_layout_dark_dias(fig), df_mot

def plot_heatmap_recorrencia(df, entidade='Motorista'):
    if df.empty or 'Periodo' not in df.columns:
        return None, pd.DataFrame()
        
    df_valido = df[~df[entidade].str.upper().isin(['NÃO IDENTIFICADO', 'NAN', '', 'N/A'])].copy()
    if df_valido.empty:
        return None, pd.DataFrame()
        
    df_pivot = df_valido.pivot_table(
        index=entidade, 
        columns='Periodo', 
        values='Quantidade', 
        aggfunc='sum', 
        fill_value=0
    )
    
    if df_pivot.empty:
        return None, pd.DataFrame()
        
    df_pivot['Total'] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.sort_values(by='Total', ascending=False).drop(columns=['Total'])
    df_pivot = df_pivot.head(15)
    
    # Heatmap customizado com a função de cor Dias+ (Transição de Teal para Salmon)
    fig = px.imshow(
        df_pivot,
        labels=dict(x="Período", y=entidade, color="Volume Itens"),
        x=df_pivot.columns,
        y=df_pivot.index,
        color_continuous_scale=['#0B2E3A', '#1A5A68', '#1A8090', '#2DC5B4', '#C47A77'],
        aspect="auto"
    )
    
    fig.update_layout(title=f"Matriz de Recorrência Mensal: Top 15 {entidade}s")
    return _aplicar_layout_dark_dias(fig), df_pivot

def plot_mapa_rotas(df_coord):
    """
    Mantido por compatibilidade interna. 
    Nota: Mapas geográficos com Mapbox geralmente exigem uma composição de estilo dark específica.
    """
    if df_coord.empty or not {'latitude', 'longitude', 'Total_Volume'}.issubset(df_coord.columns):
        return None
        
    fig = px.scatter_mapbox(
        df_coord, 
        lat="latitude", 
        lon="longitude", 
        size="Total_Volume", 
        color="Total_Volume",
        color_continuous_scale=DIAS_TEAL_SCALE, 
        size_max=30, 
        zoom=7,
        hover_name="Cidade", 
        hover_data=["Bairro", "Total_Volume"]
    )
    
    fig.update_layout(
        mapbox_style="carto-darkmatter", # Combina perfeitamente com o Dark Mode do Dias+
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#ffffff")
    )
    return fig

def plot_evolucao_temporal(df, periodicidade='M'):
    if df.empty or 'data_filtro' not in df.columns:
        return None
        
    df_time = df.copy()
    if periodicidade == 'W':
        df_time['Periodo_Agrupado'] = df_time['data_filtro'].dt.to_period('W').astype(str)
        titulo = "Evolução Temporal Semanal por Filial"
    else:
        df_time['Periodo_Agrupado'] = df_time['Periodo']
        titulo = "Evolução Temporal Mensal por Filial"
        
    df_grp = df_time.groupby(['Periodo_Agrupado', 'Filial'])['Quantidade'].sum().reset_index()
    
    # Ordem cronológica forçada
    meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    if periodicidade == 'M':
        df_grp['Periodo_Agrupado'] = pd.Categorical(df_grp['Periodo_Agrupado'], categories=meses_ordem, ordered=True)
        df_grp = df_grp.sort_values('Periodo_Agrupado')
        
    fig = px.line(
        df_grp, x='Periodo_Agrupado', y='Quantidade', color='Filial', 
        markers=True, title=titulo, color_discrete_sequence=DIAS_TEAL_SCALE
    )
    
    fig.update_layout(xaxis_title="Período", yaxis_title="Volume de Itens (Qtd)", hovermode="x unified", legend_title="Filial")
    return _aplicar_layout_dark_dias(fig)
    
def plot_comparativo_temporal_tipo(df):
    if df.empty or 'Periodo' not in df.columns:
        return None
        
    df_grp = df.groupby(['Periodo', 'Tipo_Ocorrencia'])['Quantidade'].sum().reset_index()
    
    meses_ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_grp['Periodo'] = pd.Categorical(df_grp['Periodo'], categories=meses_ordem, ordered=True)
    df_grp = df_grp.sort_values('Periodo')
    
    # Comparativo lado a lado estruturado em Teal x Salmon
    fig = px.bar(
        df_grp, 
        x='Periodo', 
        y='Quantidade', 
        color='Tipo_Ocorrencia', 
        barmode='group',
        title="Comparativo Mensal: Danos vs Faltas (Volume de Itens)",
        color_discrete_map={'Dano': COLOR_TEAL_MAIN, 'Falta': COLOR_RED_MAIN}
    )
    
    fig.update_layout(xaxis_title="Mês", yaxis_title="Quantidade de Itens", legend_title="Tipo Ocorrência")
    return _aplicar_layout_dark_dias(fig)
