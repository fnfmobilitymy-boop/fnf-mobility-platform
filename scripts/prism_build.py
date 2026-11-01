"""Apply the new hero/scroll story without rewriting the retained application."""
def apply_prism(app,component):
 needle='kennyJsx(Z.jsxs,`section`,{id:`home`,className:`hero-section`'
 start=app.index(needle);begin=app.index('(',start);depth=0;quote=None;escape=False;end=None
 for index in range(begin,len(app)):
  char=app[index]
  if quote:
   if escape:escape=False
   elif char=='\\':escape=True
   elif char==quote:quote=None
   continue
  if char in ['"',"'",'`']:quote=char;continue
  if char=='(':depth+=1
  elif char==')':
   depth-=1
   if depth==0:end=index+1;break
 if end is None or app[end:end+1]!=',':raise ValueError('Retained homepage hero shape changed')
 replacement="kennyJsx(Z.jsx,KennyPrismHero,{language:siteLanguage,onExplore:()=>S(`projects`),onContact:()=>S(`project-brief`)}),kennyJsx(Z.jsx,KennyPrismStory,{language:siteLanguage,introduction:kennyJsx(Z.jsx,Pc,{muted:r||a!==`experience`,suspended:v,reduced:_,language:t,onIntroEnd:()=>c(!0)})})"
 app=app[:start]+replacement+app[end:]
 app=app.replace('kennyJsx(Z.jsx,KennyProjectBrief,{language:siteLanguage})','kennyJsx(Z.jsx,KennyPrismReviews,{language:siteLanguage}),kennyJsx(Z.jsx,KennyProjectBrief,{language:siteLanguage})',1)
 insert=app.index('function Al(){')
 return app[:insert]+component+'\n'+app[insert:]
