import streamlit as st
import pandas as pd
from logic import buscar_leads

# Configuração da Página
st.set_page_config(page_title="CuboLeads Extractor", layout="wide")

# Cabeçalho
st.title("🟦 CuboLeads - Extrator de Oportunidades")
st.markdown("""
<style>
    .big-font { font-size:20px !important; }
</style>
<div class="big-font">
    Encontre clientes que <b>precisam</b> dos serviços da Cubo Virtual.
</div>
""", unsafe_allow_html=True)

# Esconde elementos padrão do Streamlit
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            div[data-testid="stToolbar"] {visibility: hidden;}
            div[data-testid="stDecoration"] {visibility: hidden;}
            div[data-testid="stStatusWidget"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.divider()

# Barra Lateral (Inputs)
with st.sidebar:
    st.header("Configuração da Busca")
    ramo = st.text_input("Ramo de Atividade", "Dentistas")
    cidade = st.text_input("Cidade / Região", "Sumaré, SP")
    
    st.info("O sistema buscará empresas e analisará se possuem site, SSL, Instagram e Pixel.")
    
    botao_buscar = st.button("🔍 Rastrear Oportunidades", type="primary")

# Área Principal
if botao_buscar:
    if not ramo or not cidade:
        st.warning("Por favor, preencha o Ramo e a Cidade.")
    else:
        with st.spinner(f'Buscando {ramo} em {cidade} e analisando sites... (Isso pode levar uns segundos)'):
            try:
                # Chama a função do arquivo logic.py
                df_leads = buscar_leads(ramo, cidade)
                
                # Métricas
                total = len(df_leads)
                sem_site = len(df_leads[df_leads['Site'] == 'NÃO POSSUI'])
                alta_urgencia = len(df_leads[df_leads['Urgência (0-100)'] >= 50])
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Leads Encontrados", total)
                c2.metric("Sem Site (Venda Fácil)", sem_site)
                c3.metric("Alta Urgência", alta_urgencia)
                
                st.success("Busca Concluída!")
                
                # Exibe a Tabela
                st.dataframe(
                    df_leads, 
                    use_container_width=True,
                    column_config={
                        "Site": st.column_config.LinkColumn("Site"),
                        "Urgência (0-100)": st.column_config.ProgressColumn(
                            "Nível de Oportunidade",
                            format="%d",
                            min_value=0,
                            max_value=100,
                        ),
                    }
                )
                
                # Botão de Download
                csv = df_leads.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Planilha (Excel/CSV)",
                    data=csv,
                    file_name=f'leads_{ramo}_{cidade}.csv',
                    mime='text/csv',
                )
                
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

# Rodapé
st.markdown("---")
st.caption("Desenvolvido para Agência Cubo Virtual")