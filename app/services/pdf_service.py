import os
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.fonts import addMapping
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


def generate_rental_contract(contract_data):
    """
    Gera um contrato de arrendamento em PDF.
    
    contract_data: dicionário com os dados do contrato
    Retorna: caminho do ficheiro PDF gerado
    """
    
    # Criar pasta para contratos se não existir
    contracts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'contracts')
    os.makedirs(contracts_dir, exist_ok=True)
    
    # Nome do ficheiro
    filename = f"contrato_{contract_data['property_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(contracts_dir, filename)
    
    # Criar o PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Centralizado
        spaceAfter=20
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Conteúdo do PDF
    story = []
    
    # Título
    story.append(Paragraph("CONTRATO DE ARRENDAMENTO", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Data
    story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Partes envolvidas
    story.append(Paragraph("1. PARTES ENVOLVIDAS", subtitle_style))
    story.append(Paragraph(f"<b>Senhorio (Locador):</b> {contract_data['landlord_name']}", styles['Normal']))
    story.append(Paragraph(f"<b>Inquilino (Locatário):</b> {contract_data['tenant_name']}", styles['Normal']))
    story.append(Paragraph(f"<b>BI do Inquilino:</b> {contract_data.get('tenant_bi', 'Não informado')}", styles['Normal']))
    story.append(Paragraph(f"<b>Telefone do Inquilino:</b> {contract_data.get('tenant_phone', 'Não informado')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Imóvel
    story.append(Paragraph("2. DESCRIÇÃO DO IMÓVEL", subtitle_style))
    story.append(Paragraph(f"<b>Título:</b> {contract_data['property_title']}", styles['Normal']))
    story.append(Paragraph(f"<b>Endereço:</b> {contract_data['property_address']}", styles['Normal']))
    story.append(Paragraph(f"<b>Renda Mensal:</b> {contract_data['property_rent']:,.0f} Kz", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Prazo
    story.append(Paragraph("3. PRAZO DO CONTRATO", subtitle_style))
    story.append(Paragraph(f"<b>Início:</b> {contract_data['start_date'].strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"<b>Término:</b> {contract_data['end_date'].strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"<b>Duração:</b> {contract_data['duration_months']} meses", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Condições de pagamento
    story.append(Paragraph("4. CONDIÇÕES DE PAGAMENTO", subtitle_style))
    story.append(Paragraph(f"<b>Dia de vencimento:</b> Dia {contract_data['payment_day']} de cada mês", styles['Normal']))
    story.append(Paragraph(f"<b>Valor da caução:</b> {contract_data.get('security_deposit', 0):,.0f} Kz", styles['Normal']))
    story.append(Paragraph("<b>Forma de pagamento:</b> Transferência bancária / Depósito / Numerário", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Obrigações
    story.append(Paragraph("5. OBRIGAÇÕES DO SENHORIO", subtitle_style))
    story.append(Paragraph("• Manter o imóvel em condições de habitabilidade", styles['Normal']))
    story.append(Paragraph("• Realizar reparos estruturais necessários", styles['Normal']))
    story.append(Paragraph("• Respeitar a privacidade do inquilino", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("6. OBRIGAÇÕES DO INQUILINO", subtitle_style))
    story.append(Paragraph("• Pagar a renda em dia", styles['Normal']))
    story.append(Paragraph("• Zelar pela conservação do imóvel", styles['Normal']))
    story.append(Paragraph("• Não realizar obras sem autorização", styles['Normal']))
    story.append(Paragraph("• Permitir vistorias periódicas", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Cláusulas adicionais
    if contract_data.get('additional_clauses'):
        story.append(Paragraph("7. CLÁUSULAS ADICIONAIS", subtitle_style))
        story.append(Paragraph(contract_data['additional_clauses'].replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    
    # Rescisão
    story.append(Paragraph("8. RESCISÃO", subtitle_style))
    story.append(Paragraph("O presente contrato pode ser rescindido mediante aviso prévio de 30 dias por qualquer uma das partes.", styles['Normal']))
    story.append(Paragraph("Em caso de descumprimento das cláusulas, o contrato poderá ser rescindido imediatamente.", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Assinaturas
    story.append(Paragraph("9. ASSINATURAS", subtitle_style))
    story.append(Spacer(1, 1*cm))
    
    # Tabela de assinaturas
    signatures_data = [
        ["", ""],
        ["Assinatura do Senhorio", "Assinatura do Inquilino"],
        ["_________________________", "_________________________"],
        [f"{contract_data['landlord_name']}", f"{contract_data['tenant_name']}"],
        ["", ""],
        ["Data: ___/___/_____", "Data: ___/___/_____"]
    ]
    
    signatures_table = Table(signatures_data, colWidths=[8*cm, 8*cm])
    signatures_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('TOPPADDING', (0, 2), (-1, 2), 20),
    ]))
    story.append(signatures_table)
    
    # Rodapé
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<i>Documento gerado eletronicamente pela plataforma Casa Direta.</i>", styles['Italic']))
    
    # Gerar PDF
    doc.build(story)
    
    return filename