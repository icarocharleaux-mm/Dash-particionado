import streamlit as st
import pandas as pd

# 🚨 MODO DESENVOLVEDOR: Desliguei o cache (@st.cache_data) temporariamente!
# Agora, toda vez que você der F5 no navegador, ele vai ler as planilhas do zero.
def load_data():
    mapa_meses_num = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    # ✨ FUNÇÃO UNIVERSAL DE DATAS
    def processar_mes(valor):
        if pd.isna(valor) or str(valor).strip() == '' or str(valor).lower() == 'nan':
            return 'Não Identificado'
        
        v_str = str(valor).strip()
        
        # 1. Tenta converter para número (Resolve o "1" e o "1.0")
        try:
            num = float(v_str)
            if num.is_integer() and 1 <= int(num) <= 12:
                return mapa_meses_num[int(num)]
        except ValueError:
            pass 
        
        # 2. Se for uma data (ex: "01/01/2026" ou "2026-03-01")
        try:
            dt = pd.to_datetime(v_str, dayfirst=True)
            return mapa_meses_num[dt.month]
        except:
            return 'Não Identificado'

    # ==========================================
    # 1. CARREGAR DANOS (base_pronta.csv)
    # ==========================================
    try:
        df_danos = pd.read_csv("base_pronta.csv", sep=";", encoding="latin-1")
        
        # 🛡️ O ESPANADOR DE FANTASMAS DO EXCEL: Remove caracteres invisíveis (\ufeff)
        df_danos.columns = [str(c).replace('\ufeff', '').replace('ï»¿', '').strip().lower() for c in df_danos.columns]
        
        df_danos = df_danos.rename(columns={
            'motorista': 'Motorista', 'motorista última viagem': 'Motorista',
            'filial': 'Filial', 'id_rota': 'Rota', 'qtd_reclamada': 'Quantidade', 
            'data_ref': 'Data_Original', 'cliente': 'Cliente', 'name1': 'Cliente',
            'pedido': 'Pedido', 'empresa': 'Empresa', 'categoria': 'Categoria'
        })
        
        if 'Data_Original' in df_danos.columns:
            df_danos['Periodo'] = df_danos['Data_Original'].apply(processar_mes)
            df_danos['Data_Filtro'] = pd.to_datetime(df_danos['Data_Original'], dayfirst=True, errors='coerce')
        else:
            print("⚠️ [DEBUG] Coluna 'data_ref' NÃO FOI ENCONTRADA nos Danos. Colunas lidas:", df_danos.columns.tolist())
            df_danos['Periodo'] = 'Não Identificado'
            df_danos['Data_Filtro'] = pd.NaT
            
        df_danos['Tipo_Ocorrencia'] = 'Dano'
        df_danos['Canal'] = 'N/A'
    except Exception as e:
        print(f"⚠️ [DEBUG] Erro ao carregar base de danos: {e}")
        df_danos = pd.DataFrame()

    # ==========================================
    # 2. CARREGAR FALTAS (base_falta_pronta.csv)
    # ==========================================
    try:
        df_faltas = pd.read_csv("base_falta_pronta.csv", sep=";", encoding="latin-1")
        
        # 🛡️ O ESPANADOR DE FANTASMAS DO EXCEL
        df_faltas.columns = [str(c).replace('\ufeff', '').replace('ï»¿', '').strip().lower() for c in df_faltas.columns]

        df_faltas = df_faltas.rename(columns={
            'motorista ultima viagem': 'Motorista', 'motorista última viagem': 'Motorista',
            'name1': 'Cliente', 'cliente': 'Cliente', 'filial': 'Filial', 
            'rota': 'Rota', 'cantidad_itens': 'Quantidade', 'mes': 'Mes_Original', 
            'nm_pedido': 'Pedido', 'marca_canal': 'Canal', 'categoria': 'Categoria'
        })

        if 'Mes_Original' in df_faltas.columns:
            df_faltas['Periodo'] = df_faltas['Mes_Original'].apply(processar_mes)
            df_faltas['Data_Filtro'] = pd.to_datetime(df_faltas['Mes_Original'], dayfirst=True, errors='coerce')
        else:
            print("⚠️ [DEBUG] Coluna 'mes' NÃO FOI ENCONTRADA nas Faltas. Colunas lidas:", df_faltas.columns.tolist())
            df_faltas['Periodo'] = 'Não Identificado'
            df_faltas['Data_Filtro'] = pd.NaT
            
        df_faltas['Tipo_Ocorrencia'] = 'Falta'
        df_faltas['Empresa'] = 'NATURA'
    except Exception as e:
        print(f"⚠️ [DEBUG] Erro ao carregar base de faltas: {e}")
        df_faltas = pd.DataFrame()

    # ==========================================
    # 3. UNIFICAR E BLINDAR
    # ==========================================
    colunas_comuns = ['Cliente', 'Pedido', 'Motorista', 'Filial', 'Categoria', 'Rota', 'Tipo_Ocorrencia', 'Quantidade', 'Periodo', 'Empresa', 'Canal', 'Data_Filtro']
    
    for df in [df_danos, df_faltas]:
        if not df.empty:
            for col in colunas_comuns:
                if col not in df.columns: 
                    if col == 'Data_Filtro':
                        df[col] = pd.NaT
                    else:
                        df[col] = 'Não Identificado'
                # Preenche vazios apenas nas colunas que não são de data
                if col != 'Data_Filtro':
                    df[col] = df[col].fillna('Não Identificado')

    df_unificado = pd.concat([df_danos[colunas_comuns], df_faltas[colunas_comuns]], ignore_index=True)
    
    if not df_unificado.empty and 'Rota' in df_unificado.columns:
        df_unificado['Rota'] = df_unificado['Rota'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    # ==========================================
    # 4. CARREGAR MAPAS E TRATATIVAS
    # ==========================================
    try:
        df_coord = pd.read_csv("base_coordenadas.csv", sep=";", encoding="latin-1", skiprows=7, decimal=",")
        df_coord.columns = [str(c).replace('\ufeff', '').strip() for c in df_coord.columns]
        
        if 'ROTA' in df_coord.columns: df_coord = df_coord.rename(columns={'ROTA': 'Rota'})
        if 'Rota' not in df_coord.columns and 'rota' in df_coord.columns: df_coord = df_coord.rename(columns={'rota': 'Rota'})
        
        df_coord_agg = df_coord.groupby('Rota').agg({'LATITUDE': 'mean', 'LONGITUDE': 'mean'}).reset_index()
        
        df_mapa = pd.read_csv("rotas e bairros.csv", sep=";", encoding="latin-1", skiprows=7)
        df_mapa_agg = df_mapa.groupby('Rota').agg({'Setor': 'first', 'Bairro': lambda x: ', '.join(x.dropna().unique()[:3])}).reset_index()
    except Exception as e:
        print(f"⚠️ [DEBUG] Erro no Mapa/Coordenadas: {e}")
        df_coord_agg, df_mapa_agg = pd.DataFrame(), pd.DataFrame()

    try:
        df_trat1 = pd.read_csv("Tratativas.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
        df_trat2 = pd.read_csv("tratativas2.csv", sep=";", encoding="latin-1").dropna(subset=['MOTORISTA'])
    except Exception:
        df_trat1, df_trat2 = pd.DataFrame(), pd.DataFrame()

    return df_danos, df_faltas, df_unificado, df_mapa_agg, df_coord_agg, df_trat1, df_trat2
