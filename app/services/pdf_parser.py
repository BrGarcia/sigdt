import fitz
import re
import os

def clean_text(text):
    """Limpeza refinada para remover ruídos de rodapé, campos vazios e duplicatas"""
    stop_words = [
        r"Amostra:", 
        r"Anexo:", 
        r"Pág\.:", 
        r"COMANDO DA AERONÁUTICA",
        r"Serviço Solicitado:"
    ]
    
    for word in stop_words:
        pattern = re.compile(word, re.IGNORECASE)
        match = pattern.search(text)
        if match:
            text = text[:match.start()]

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    seen = set()
    unique_lines = []
    for line in lines:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)
            
    return "\n".join(unique_lines)

def parse_at_pdf(pdf_path: str) -> dict:
    """Extrai todas as informações relevantes do PDF de uma Ficha AT de forma robusta."""
    if not os.path.exists(pdf_path):
        return {"error": f"Arquivo não encontrado: {pdf_path}"}

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text", sort=True) + "\n"
        doc.close()
    except Exception as e:
        return {"error": f"Erro ao processar PDF: {e}"}

    patterns = [
        ("Ficha A.T.", r"Ficha A\.T\.:\s*(\S+)"),
        ("Cód. Assessoramento", r"Cód\. Assessoramento:\s*(\S+)"),
        ("Data Solicitacao", r"Data Solicitacao:\s*([\d/]+)"),
        ("OM Origem", r"OM Origem:\s*(\S+)"),
        ("Solicitante", r"Solicitante:\s*(.*?)\s+OM Destino:"),
        ("OM Destino", r"OM Destino:\s*(\S+)"),
        ("Chefe de Oficina", r"Chefe de Oficina:\s*(.*?)\s+Situação:"),
        ("Situação", r"Situação:\s*(\S+)"),
        ("Data Autorização TENG", r"Data Autorização TENG:\s*([\d/]+)"),
        ("PN", r"IDENTIFICAÇÃO DO ITEM.*?\bPN:\s*(.*?)\s+CFF:"),
        ("CFF", r"IDENTIFICAÇÃO DO ITEM.*?CFF:\s*(.*?)\s+Nomenclatura:"),
        ("Nomenclatura", r"IDENTIFICAÇÃO DO ITEM.*?Nomenclatura:\s*(.*?)\s+SN:"),
        ("SN", r"IDENTIFICAÇÃO DO ITEM.*?SN:\s*(\S+)"),
        ("Sistema", r"Sistema:\s*(.*?)\s+Projeto:"),
        ("Projeto", r"Projeto:\s*(\S+)"),
        ("Analista ou Responsável", r"Analista ou Responsável:.*?\n+(.*?)\n+Função"),
        ("Data Análise", r"Analista ou Responsável:.*?Data\s*:\s*([\d/]+)"),
        ("Função do Analista", r"Função:\s*(.*?)\s*Assinatura")
    ]

    extracted_data = {}
    for key, pattern in patterns:
        match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
        val = match.group(1).strip() if match else "NÃO ENCONTRADO"
        extracted_data[key] = val

    # Extração dos blocos de texto grandes
    match_servico = re.search(r"Serviço Solicitado:(.*?)(?:Amostra:|Anexo:|Parecer da Engenharia:|Preenchido pela Engenharia)", full_text, re.DOTALL | re.IGNORECASE)
    servico_raw = match_servico.group(1).strip() if match_servico else "NÃO ENCONTRADO"
    extracted_data["Serviço Solicitado"] = clean_text(servico_raw).replace('\n', ' ')

    match_parecer = re.search(r"Parecer da Engenharia:(.*?)(?:LOCAIS PARA DISTRIBUIÇÃO|PARTICIPANTES|$)", full_text, re.DOTALL | re.IGNORECASE)
    parecer_raw = match_parecer.group(1).strip() if match_parecer else "NÃO ENCONTRADO"
    extracted_data["Parecer da Engenharia"] = clean_text(parecer_raw).replace('\n', ' ')

    return extracted_data
