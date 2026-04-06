import plotly.express as px

def plot_top_motoristas(df_filtrado, escala_cor):
    """Gera o gráfico de barras horizontais do Top 10 Motoristas com hover da filial."""
    if df_filtrado.empty:
        return None
        
    ranking = df_filtrado.groupby('Motorista')['Quantidade'].sum().nlargest(10).reset_index()
    filial_map = df_filtrado.groupby("Motorista")["Filial"].agg(lambda x: x.value_counts().index[0] if not x.empty else "N/A").to_dict()
    ranking["Filial"] = ranking["Motorista"].map(filial_map)
    
    fig = px.bar(ranking, x='Quantidade', y='Motorista', orientation='h', 
                 color='Quantidade', color_continuous_scale=escala_cor,
                 hover_data=['Filial'])
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    return fig

def plot_comparativo_filial(df_filtrado, escala_cor):
    """Gera o gráfico de barras verticais do comparativo entre filiais."""
    if df_filtrado.empty:
        return None
        
    contagem = df_filtrado.groupby("Filial")["Quantidade"].sum().reset_index().sort_values("Quantidade", ascending=False)
    fig = px.bar(contagem, x='Filial', y='Quantidade', text='Quantidade', 
                 color='Quantidade', color_continuous_scale=escala_cor)
    fig.update_layout(xaxis={'categoryorder':'total descending'}, showlegend=False)
    return fig

def plot_pizza_tipo_ocorrencia(df_filtrado):
    """Gera o gráfico de pizza Dano x Falta."""
    if df_filtrado.empty:
        return None
        
    pizza = df_filtrado.groupby('Tipo_Ocorrencia')['Quantidade'].sum().reset_index()
    fig = px.pie(pizza, names='Tipo_Ocorrencia', values='Quantidade', hole=0.4, 
                 color_discrete_map={'Dano':'#1f77b4', 'Falta':'#d62728'})
    return fig