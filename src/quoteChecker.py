import re
import unicodedata

def change_quote_num(txt, addnum):
  txtNumStrList = re.findall(r'\(\*\d+', txt)
  for txtNumStr in txtNumStrList:
    txtNum = [x for x in txtNumStr if x.isdigit()]
    txtNum = int(''.join(txtNum))
    txt = txt.replace(txtNumStr, f'(*{txtNum+addnum}')
  return txt

def print_quote(rearr_context_doc, docs, verbose:bool=True):
  txtNumStrList = re.findall(r'\*\d+', rearr_context_doc.page_content)
  txtNumList = []
  for txtNumStr in txtNumStrList:
    txtNum = [x for x in txtNumStr if x.isdigit()]
    txtNum = int(''.join(txtNum))
    txtNumList.append(txtNum)
  txtNumList = list(set(txtNumList)).sort()

  '''주석 표시'''
  quoteList = []
  for txtNum in txtNumList:
    #간혹 AI가 부여한 참조 번호가 잘못된 경우, 주석 표기 취소
    if txtNum > len(docs):
      continue
    doc = docs[txtNum-1]
    quote = f"(*{txtNum}){unicodedata.normalize('NFC',doc.metadata['source'].replace('/',''))}. {int(doc.metadata['page'])+1}pg"
    quoteList.append(quote)

  if verbose:
    print('출처: ', '; '.join(quoteList))

  return '출처: ', '; '.join(quoteList)