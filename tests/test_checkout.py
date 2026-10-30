"""Monetary rounding and approved catalogue boundaries, independent of markup."""
import unittest,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source/seo'))
from catalogue import catalogue
class CheckoutTests(unittest.TestCase):
 def test_catalogue(self):
  for lang in ['en','zh','ms']:
   items=catalogue(lang);self.assertEqual(len(items),30);self.assertEqual(len({p['id'] for p in items}),30)
   by={p['id']:p for p in items};self.assertEqual(by['addon-8']['min'],5);self.assertEqual(by['addon-6']['setup']+by['addon-6']['price']*3,950)
   self.assertEqual([by[x]['price'] for x in ['essential','signature','personal','business','ecommerce']],[1000,1800,1800,2500,4500])
 def test_stage_money(self):
  code="""const a=require('node:assert/strict'),m=require('./source/payments/calculation.js');a.equal(m.calculate('1000','deposit','stripe').totalCents,53000);a.equal(m.calculate('1234.56','deposit','stripe').totalCents,65432);for(let q=10001;q<10100;q++){const amount=(q/100).toFixed(2);a.equal(['deposit','second','balance'].reduce((n,p)=>n+m.calculate(amount,p,'bank').baseCents,0),q)}for(const method of ['bank','tng','usdt'])a.equal(m.calculate('1000','deposit',method).feeCents,0);for(const bad of ['-1','1e3','0','1.234','NaN','1000001'])a.throws(()=>m.calculate(bad,'deposit','bank'));"""
  subprocess.run(['node','-e',code],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
