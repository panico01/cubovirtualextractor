import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import urllib3

# Desabilita avisos de SSL se necessário (para não poluir o terminal)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Apenas para teste local rápido (mas apague antes de subir se for público)
    # O ideal é criar um arquivo .streamlit/secrets.toml localmente
    st.error("Chave de API não configurada!")

def analisar_site(url):
    """
    Verifica se o site tem falhas.
    Agora segue redirecionamentos para verificar se o link final é HTTPS.
    """
    problemas = []
    
    # Caso 1: Não tem site cadastrado no Google
    if not url:
        return ["SEM SITE (Oportunidade Alta)"], 50
    
    try:
        # Configuração para parecer um navegador real (evita bloqueios)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        # Tenta acessar com timeout maior (10s) para sites lentos
        # verify=False ajuda a acessar sites com erro de certificado para podermos analisar o HTML mesmo assim
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        
        # O site abriu? Vamos ver o conteúdo.
        if response.status_code == 200:
            
            # --- VERIFICAÇÃO DE SEGURANÇA (SSL) ---
            # Verifica a URL FINAL. Se o site redirecionou para HTTPS, está seguro.
            url_final = response.url
            if not url_final.startswith("https"):
                problemas.append("SITE INSEGURO (Não usa HTTPS)")
            
            # --- ANÁLISE DO CONTEÚDO (HTML) ---
            texto_html = response.text.lower()
            
            # Verifica Redes Sociais no código fonte
            if 'instagram.com' not in texto_html:
                problemas.append("Sem link para Instagram")
            
            # Verifica WhatsApp (links comuns)
            if 'wa.me' not in texto_html and 'api.whatsapp.com' not in texto_html:
                problemas.append("Sem link direto WhatsApp")
                
            # Verifica Pixel do Facebook
            if 'fbevents.js' not in texto_html and 'connect.facebook.net' not in texto_html:
                problemas.append("Sem Pixel Facebook")
                
        else:
            # Site respondeu, mas com erro (ex: 404, 500)
            return [f"SITE COM ERRO (Código {response.status_code})"], 40
            
    except requests.exceptions.SSLError:
        return ["CERTIFICADO INVÁLIDO/EXPIRADO"], 45
    except requests.exceptions.ConnectionError:
        return ["SITE NÃO ABRE / SERVIDOR OFF"], 50
    except requests.exceptions.Timeout:
        return ["SITE MUITO LENTO (Timeout)"], 30
    except Exception as e:
        return ["ERRO DESCONHECIDO AO ACESSAR"], 30

    # Calcula score base
    score = len(problemas) * 15
    if not problemas:
        return ["Site OK (Seguro e Otimizado)"], 0
        
    return problemas, score

def buscar_leads(termo, local):
    """Função principal chamada pelo App"""
    try:
        url_busca = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={termo}+em+{local}&key={API_KEY}"
        resp = requests.get(url_busca).json()
        resultados = resp.get('results', [])
        
        lista_final = []
        
        for place in resultados:
            place_id = place['place_id']
            
            url_detalhe = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website,formatted_address&key={API_KEY}"
            detalhe_resp = requests.get(url_detalhe).json()
            detalhe = detalhe_resp.get('result', {})
            
            nome = detalhe.get('name')
            site = detalhe.get('website') # Pode ser None
            fone = detalhe.get('formatted_phone_number', 'N/A')
            endereco = detalhe.get('formatted_address', 'N/A')
            
            # Chama a nova função de análise
            falhas, urgencia = analisar_site(site)
            
            if not site:
                site = "NÃO POSSUI"
                urgencia = 100
            
            lista_final.append({
                "Empresa": nome,
                "Urgência (0-100)": urgencia,
                "Problemas Detectados": ", ".join(falhas),
                "Telefone": fone,
                "Site": site,
                "Endereço": endereco
            })
            
        df = pd.DataFrame(lista_final)
        if not df.empty:
            df = df.sort_values(by="Urgência (0-100)", ascending=False)
            
        return df
        
    except Exception as e:
        print(f"Erro na busca: {e}")
        return pd.DataFrame() # Retorna vazio se der erro geral