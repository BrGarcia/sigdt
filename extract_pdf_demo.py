from app.services.pdf_parser import parse_at_pdf
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import sys

# Run the parser
result = parse_at_pdf("modelo_at.pdf")

doc = SimpleDocTemplate("resultado_extracao.pdf", pagesize=letter)
styles = getSampleStyleSheet()
Story = []

if "error" in result:
    Story.append(Paragraph(f"Erro: {result['error']}", styles['Normal']))
else:
    Story.append(Paragraph("RELATORIO DE INFORMACOES EXTRAIDAS - SIGDT", styles['Title']))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph(f"<b>Ficha AT:</b> {result.get('num_at', 'N/A')}", styles['Normal']))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("<b>SERVICO SOLICITADO:</b>", styles['Heading3']))
    # Safe newline replacement for HTML-like reportlab paragraphs
    servico = str(result.get('servico', '')).replace('\n', '<br />')
    Story.append(Paragraph(servico, styles['Normal']))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph("<b>PARECER DA ENGENHARIA:</b>", styles['Heading3']))
    parecer = str(result.get('parecer', '')).replace('\n', '<br />')
    Story.append(Paragraph(parecer, styles['Normal']))
    
doc.build(Story)
print("✅ Arquivo PDF gerado com sucesso em: resultado_extracao.pdf")
