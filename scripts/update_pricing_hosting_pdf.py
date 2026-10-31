"""Update the bilingual customer guide with the approved first-year/renewal policy."""
from pathlib import Path
from datetime import date
import sys,fitz
from fontTools.ttLib import TTFont
from fontTools import subset
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source/seo'))
from pricing import HOSTING,HOSTING_NOTES
from policy import CLAUSES,VERSION
PDF=ROOT/'media/kenny-studio-pricing-en-zh.pdf'
rows=[(name[0]+' | '+name[1],price[0]+'\n'+price[1],scope[0]+'\n'+scope[1]) for name,price,scope in HOSTING]
patches={3:[(170,'展示型静态套餐含首年基础托管；服务器／平台订阅、续费和维护按后附明细另计。'),(185,'Static showcase plans include first-year basic hosting. Server/platform fees, renewals and care follow the supplement.')],5:[(578,'普通域名首年已含；特别域名差额、续费与服务器托管按后附明细另计。'),(590,'Standard domain: first year included. Premium-domain extras, renewals and server hosting follow the supplement.')]}
extra=['HOSTING & DOMAIN','First year, clearly included.','Renewals, clearly priced.','首年包含与后续续费明细','K+ KENNY STUDIO','SERVICE & PRICE GUIDE · HOSTING / DOMAIN UPDATE','MYR · EN / 中文','See the original maintenance package for included hours. No duplicate fees.','维护时数按原套餐执行，已含项目不重复收费。','Domain ownership stays with the customer.','域名归客户所有。','hello@kennystudio.cfd','kennystudio.cfd','Maintenance / 维护：RM150 / month 起','Includes one ordinary domain for the first year; eligible suffix and registration budget are agreed in writing.','各网站套餐含普通域名首年，适用后缀和注册预算书面确认。']
text=''.join(''.join(r) for r in rows)+''.join(''.join(x) for x in patches.values() for x in [(str(t[0]),t[1]) for t in x])+''.join(extra)+''.join(n[0]+n[1] for n in HOSTING_NOTES)
text+=''.join(h[0]+h[1]+b[0]+b[1] for h,b in CLAUSES)+'Project policy & mutual protection项目政策与双方保障'+VERSION
font=TTFont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',fontNumber=2);options=subset.Options();options.layout_features=[];options.retain_gids=True;sub=subset.Subsetter(options=options);sub.populate(text=text);sub.subset(font);font_path=Path('/tmp/kenny-price-supplement.otf');font.save(font_path)
doc=fitz.open(PDF)
if len(doc)>8:doc.delete_pages(8,len(doc)-1)
bg=(.976,.973,.985);ink=(.12,.09,.18);purple=(.48,.28,.85);muted=(.4,.36,.46)
def put(page,rect,text,size=9,color=ink):
 result=page.insert_textbox(fitz.Rect(rect),text,fontname='hostingcjk',fontfile=str(font_path),fontsize=size,lineheight=1.4,color=color)
 if result<0:raise RuntimeError('PDF content does not fit: '+text[:80])
for index,lines in patches.items():
 p=doc[index];p.insert_font(fontname='hostingcjk',fontfile=str(font_path))
 for y,text in lines:p.add_redact_annot(fitz.Rect(50,y-2,548,y+15),fill=bg)
 p.apply_redactions()
 for y,text in lines:put(p,(51,y-1,548,y+17),text,6.5,muted)
# Domain and hosting get separate, spacious bilingual pages.
for page_no,indices in [(9,[2,3,4]),(10,[0,1,5])]:
 p=doc.new_page(width=595,height=842);p.draw_rect(p.rect,color=None,fill=bg);p.insert_font(fontname='hostingcjk',fontfile=str(font_path))
 put(p,(42,35,550,58),'K+ KENNY STUDIO',11,purple)
 p.draw_line((42,68),(552,68),color=(.83,.79,.89),width=.6)
 put(p,(42,86,550,116),'HOSTING & DOMAIN',11,purple)
 put(p,(42,118,552,168),'First year, clearly included.' if page_no==9 else 'Renewals, clearly priced.',23)
 put(p,(42,170,550,198),'首年包含与后续续费明细',13)
 y=218
 for index in indices:
  title,price,scope=rows[index]
  p.draw_rect(fitz.Rect(42,y,553,y+147),color=(.85,.81,.9),fill=(.95,.936,.97),width=.5)
  put(p,(55,y+10,540,y+40),title,10,purple)
  put(p,(55,y+44,540,y+78),price,9)
  put(p,(55,y+80,540,y+143),scope,7.5)
  y+=159
 note=HOSTING_NOTES[1 if page_no==9 else 0]
 put(p,(42,704,550,785),note[0]+'\n'+note[1],8,muted)
 p.draw_line((42,800),(552,800),color=(.83,.79,.89),width=.6)
 put(p,(42,808,550,833),'kennystudio.cfd  |  hello@kennystudio.cfd  |  '+str(page_no)+'/13',7,muted)
for group in range(3):
 p=doc.new_page(width=595,height=842);p.draw_rect(p.rect,color=None,fill=bg);p.insert_font(fontname='hostingcjk',fontfile=str(font_path))
 put(p,(42,35,550,58),'K+ KENNY STUDIO',11,purple);p.draw_line((42,68),(552,68),color=(.83,.79,.89),width=.6)
 put(p,(42,86,550,116),'Project policy & mutual protection',15)
 put(p,(42,120,550,148),'项目政策与双方保障 · '+VERSION,10,purple)
 y=161
 for i in range(group*4,group*4+4):
  heading,body=CLAUSES[i];p.draw_rect(fitz.Rect(42,y,553,y+145),color=(.85,.81,.9),fill=(.95,.936,.97),width=.5)
  put(p,(53,y+8,541,y+37),str(i+1).zfill(2)+' / '+heading[0]+' | '+heading[1],9,purple)
  put(p,(53,y+39,541,y+141),body[0]+'\n'+body[1],7.2)
  y+=153
 p.draw_line((42,800),(552,800),color=(.83,.79,.89),width=.6)
 put(p,(42,808,550,833),'kennystudio.cfd  |  hello@kennystudio.cfd  |  '+str(11+group)+'/13',7,muted)
output=PDF.with_suffix('.new.pdf');doc.save(output,garbage=4,deflate=True);doc.close();output.replace(PDF)
print('Updated',PDF,'bytes',PDF.stat().st_size)
