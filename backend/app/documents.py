from io import BytesIO
from pathlib import Path
from datetime import datetime,timezone
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image as PDFImage
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
def render_pdf(order,stage,kind,num,issued):
 b=BytesIO();doc=SimpleDocTemplate(b,pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=45,bottomMargin=45)
 style=ParagraphStyle('body',fontName='STSong-Light',fontSize=11,leading=18,textColor=colors.HexColor('#252033'))
 title=ParagraphStyle('title',parent=style,fontSize=22,leading=30,textColor=colors.HexColor('#7550d5'))
 p=lambda text:Paragraph(escape(str(text)),style)
 amount=lambda value:'RM'+format(value/100,'.2f')
 labels={'deposit':'50% Deposit / 定金','second':'30% Development / 阶段款','balance':'20% Acceptance balance / 验收尾款'}
 logo=Path(__file__).resolve().parents[1]/'static/brand/kenny-wordmark-v1.png'
 brand=PDFImage(str(logo),width=190,height=35.4,hAlign='LEFT') if logo.exists() else Paragraph('KENNY STUDIO',title)
 story=[brand,p('hello@kennystudio.cfd · kennystudio.cfd'),Spacer(1,18),Paragraph('Payment receipt / 已付款收据' if kind=='receipt' else 'Invoice / 付款账单',title)]
 if order.get('test_mode'):story.insert(0,Paragraph('TEST ONLY / 测试单据 / NOT A REAL PAYMENT',title))
 for label,value in [('Number / 编号',num),('Issued / 签发',datetime.fromtimestamp(issued,timezone.utc).strftime('%Y-%m-%d UTC')),('Order / 订单',order['public_no']),('Customer / 客户',order['name']),('Email / 邮箱',order['email']),('Stage / 阶段',labels[stage['phase']]),('Method / 方式',stage['method'].upper())]:story.append(p(label+': '+str(value)))
 story.extend([Spacer(1,15),p('Agreed scope / 确认范围'),p(order['scope'])])
 data=[[p('Description / 明细'),p('MYR / 马币')],[p('Stage service amount / 本期服务费用'),p(amount(stage['base']))]]
 if stage['fee']:data.append([p('Stripe service fee 6% / 服务费'),p(amount(stage['fee']))])
 data.append([p('Total / 合计'),p(amount(stage['total']))]);table=Table(data,colWidths=[365,135]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eee8fa')),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#dcd6e6')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]));story.extend([Spacer(1,16),table,Spacer(1,16)])
 if stage['usdt']:story.append(p('Agreed USDT amount / 已确认 USDT: '+stage['usdt']+' · TRC20 / Tron. MYR amounts are the invoice denomination; no exchange rate is implied.'))
 story.append(p('SIMULATED TEST RECORD / 模拟测试记录，不代表实际付款。' if order.get('test_mode') else ('Funds verified / 款项已核实。 Reference: '+str(stage['reference'] or '')) if kind=='receipt' else 'Payment request only. This invoice does not prove payment. / 此账单不代表已付款。'))

 if kind=='invoice':story.append(p('Pay only when this stage is open in your project portal. / 仅在订单页面开放本阶段后付款。'))
 story.append(p('This document is not a validated LHDN e-Invoice. / 此文件不是经 LHDN 验证的电子发票。'))
 doc.build(story);return b.getvalue()
