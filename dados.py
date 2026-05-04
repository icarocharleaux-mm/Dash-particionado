import streamlit as st
import pandas as pd

def load_data():
    mapa_meses_num = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # ==========================================
    # 1. CARREGAR DANOS (base_pronta.csv)
    # ==========================================
    try:
        df_danos = pd.read_csv("base_pronta.csv", sep=";", encoding="latin-1")
        df_danos.columns = [str(c).replace('\ufeff', '').replace('ï»¿', '').strip().lower() for c in df_danos.columns]

        # Padronização imediata pela coluna 0
        if not df_danos.empty:
            # CORREÇÃO: Removido dayfirst=True para aceitar o formato YYYY-MM-DD da base
            df_danos["Data_Filtro"] = pd.to_datetime(df_danos.iloc[:, 0], errors='coerce')
            df_danos['Periodo'] = df_danos["Data_Filtro"].dt.month.map(mapa_meses_num).fillna('Não Identificado')
        else:
            df_danos["Data_Filtro"] = pd.NaT
            df_danos['Periodo'] = 'Não Identificado'

        df_danos = df_danos.rename(columns={
            'motorista': 'Motorista', 'motorista última viagem': 'Motorista',
            'filial': 'Filial', 'id_rota': 'Rota', 'qtd_reclamada': 'Quantidade', 
            'cliente': 'Cliente', 'name1': 'Cliente',
            'pedido': 'Pedido', 'empresa': 'Empresa', 'categoria': 'Categoria'
        })
            
        df_danos['Tipo_Ocorrencia'] = 'Dano'
        df_danos['Canal'] = 'N/A'
    except Exception as e:
        df_danos = pd.DataFrame()

    # ==========================================
    # 2. CARREGAR FALTAS (base_falta_pronta.csv)
    # ==========================================
    try:
        df_faltas = pd.read_csv("base_falta_pronta.csv", sep=";", encoding="latin-1")
        df_faltas.columns = [str(c).replace('\ufeff', '').replace('ï»¿', '').strip().lower() for c in df_faltas.columns]

        # Padronização imediata pela coluna 0
        if not df_faltas.empty:
            # CORREÇÃO: Removido dayfirst=True para aceitar o formato YYYY-MM-DD da base
            df_faltas["Data_Filtro"] = pd.to_datetime(df_faltas.iloc[:, 0], errors='coerce')
            df_faltas['Periodo'] = df_faltas["Data_Filtro"].dt.month.map(mapa_meses_num).fillna('Não Identificado')
        else:
            df_faltas["Data_Filtro"] = pd.NaT
            df_faltas['Periodo'] = 'Não Identificado'

        df_faltas = df_faltas.rename(columns={
            'motorista ultima viagem': 'Motorista', 'motorista última viagem': 'Motorista',
            'name1': 'Cliente', 'cliente': 'Cliente', 'filial': 'Filial', 
            'rota': 'Rota', 'cantidad_itens': 'Quantidade', 
            'nm_pedido': 'Pedido', 'marca_canal': 'Canal', 'categoria': 'Categoria'
        })
            
        df_faltas['Tipo_Ocorrencia'] = 'Falta'
        df_faltas['Empresa'] = 'NATURA'
    except Exception as e:
        df_faltas = pd.DataFrame()

    # ==========================================
    # 3. UNIFICAR E BLINDAR (Lógica de preenchimento corrigida)
    # ==========================================
    colunas_comuns = ['Cliente', 'Pedido', 'Motorista', 'Filial', 'Categoria', 'Rota', 'Tipo_Ocorrencia', 'Quantidade', 'Periodo', 'Empresa', 'Canal', 'Data_Filtro']
    
    for df in [df_danos, df_faltas]:
        if not df.empty:
            # Garante que a coluna Quantidade é numérica e substitui vazios por 0 (evita virar texto)
            if 'Quantidade' in df.columns:
                df['Quantidade'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)

            for col in colunas_comuns:
                if col not in df.columns: 
                    if col == 'Data_Filtro': df[col] = pd.NaT
                    else: df[col] = 'Não Identificado'
                
                # SÓ preenche com "Não Identificado" se NÃO for a coluna de data ou de quantidade
                if col not in ['Data_Filtro', 'Quantidade']:
                    df[col] = df[col].fillna('Não Identificado')

    df_unificado = pd.concat([df_danos[colunas_comuns], df_faltas[colunas_comuns]], ignore_index=True)
    if not df_unificado.empty and 'Rota' in df_unificado.columns:
        df_unificado['Rota'] = df_unificado['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    # ==========================================
    # 4. CARREGAR MAPAS E TRATATIVAS
    # ==========================================
    try:
        # Extraindo as coordenadas e bairros diretamente das bases oficiais!
        df_notas = pd.read_csv("relatorionotas.csv", sep=";", encoding="latin-1", skiprows=7)
        df_falta = pd.read_csv("relatorionotas_falta.csv", sep=";", encoding="latin-1", skiprows=7)
        df_ref = pd.concat([df_notas, df_falta], ignore_index=True)

        if 'Rota' in df_ref.columns:
            df_geo = df_ref[['Rota', 'Cidade', 'Bairro', 'LATITUDE', 'LONGITUDE']].dropna(subset=['Rota'])
            df_geo['LATITUDE'] = pd.to_numeric(df_geo['LATITUDE'].astype(str).str.replace(',', '.'), errors='coerce')
            df_geo['LONGITUDE'] = pd.to_numeric(df_geo['LONGITUDE'].astype(str).str.replace(',', '.'), errors='coerce')
            df_geo['Rota'] = df_geo['Rota'].astype(str).str.strip()

            df_geo_agg = df_geo.groupby('Rota').agg({
                'Cidade': lambda x: x.value_counts().index[0] if not x.dropna().empty else 'N/A',
                'Bairro': lambda x: x.value_counts().index[0] if not x.dropna().empty else 'N/A',
                'LATITUDE': 'mean',
                'LONGITUDE': 'mean'
            }).reset_index()

            # Separamos em dois dataframes para respeitar o formato original do seu return
            df_coord_agg = df_geo_agg[['Rota', 'LATITUDE', 'LONGITUDE']].copy()
            df_mapa_agg = df_geo_agg[['Rota', 'Cidade', 'Bairro']].copy()
        else:
            df_coord_agg, df_mapa_agg = pd.DataFrame(), pd.DataFrame()

    except Exception as e:
        df_coord_agg, df_mapa_agg = pd.DataFrame(), pd.DataFrame()

    try:
        df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
        df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
    except Exception:
        df_trat1, df_trat2 = pd.DataFrame(), pd.DataFrame()

    return df_danos, df_faltas, df_unificado, df_mapa_agg, df_coord_agg, df_trat1, df_trat2
