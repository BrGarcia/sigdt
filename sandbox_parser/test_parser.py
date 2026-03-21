import fitz
import re
import os

def clean_text(text):
    """Limpeza refinada para remover ruídos de rodapé, campos vazios e duplicatas"""
    # Lista de palavras que marcam o fim real do conteúdo útil
    stop_words = [
        r"Amostra:", 
        r"Anexo:", 
        r"Pág\.:", 
        r"COMANDO DA AERONÁUTICA",
        r"Serviço Solicitado:" # Caso o título se repita
    ]
    
    # Trunca o texto no primeiro stop_word encontrado
    for word in stop_words:
        pattern = re.compile(word, re.IGNORECASE)
        match = pattern.search(text)
        if match:
            text = text[:match.start()]

    # Divide em linhas e remove espaços extras
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Remove parágrafos duplicados mantendo a ordem (importante para quebras de página)
    seen = set()
    unique_lines = []
    for line in lines:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)
            
    return "\n".join(unique_lines)

def test_at_parser(pdf_path):
    if not os.path.exists(pdf_path):
        return f"Erro: Arquivo {pdf_path} não encontrado."

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text", sort=True) + "\n"
        doc.close()
    except Exception as e:
        return f"Erro ao processar PDF: {e}"

    # 1. Extrair Número da Ficha A.T.
    match_at = re.search(r"Ficha A\.T\.:\s*(\d+)", full_text, re.IGNORECASE)
    num_at = match_at.group(1).strip() if match_at else "NÃO ENCONTRADO"

    # 2. Extrair Serviço Solicitado (Parando em marcadores de interrupção)
    # A regex agora é mais restrita para evitar capturar o rodapé
    match_servico = re.search(r"Serviço Solicitado:(.*?)(?:Amostra:|Anexo:|Parecer da Engenharia:|Preenchido pela Engenharia)", full_text, re.DOTALL | re.IGNORECASE)
    servico_raw = match_servico.group(1).strip() if match_servico else "NÃO ENCONTRADO"
    servico_limpo = clean_text(servico_raw)

    # 3. Extrair Parecer da Engenharia
    match_parecer = re.search(r"Parecer da Engenharia:(.*?)(?:LOCAIS PARA DISTRIBUIÇÃO|PARTICIPANTES|$)", full_text, re.DOTALL | re.IGNORECASE)
    parecer_raw = match_parecer.group(1).strip() if match_parecer else "NÃO ENCONTRADO"
    parecer_limpo = clean_text(parecer_raw)

    # Gerar o arquivo TXT
    output_file = "resultado_extracao.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write(f"RELATÓRIO DE EXTRAÇÃO LIMPO - AT {num_at}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"NÚMERO DA FICHA A.T.: {num_at}\n\n")
        
        f.write("-" * 30 + "\n")
        f.write("[SERVIÇO SOLICITADO]\n")
        f.write("-" * 30 + "\n")
        f.write(servico_limpo + "\n\n")
        
        f.write("-" * 30 + "\n")
        f.write("[PARECER TÉCNICO / ENGENHARIA]\n")
        f.write("-" * 30 + "\n")
        f.write(parecer_limpo + "\n\n")
        
        f.write("="*60 + "\n")
        f.write("FIM DO RELATÓRIO\n")
        f.write("="*60 + "\n")

    return output_file

if __name__ == "__main__":
    resultado = test_at_parser("../modelo_at.pdf")
    print(f"Processamento concluído. Verifique o arquivo: {resultado}")
