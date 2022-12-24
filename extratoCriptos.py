# -*- coding: utf-8 -*-
import pandas as pd
import re, os

def leitura():
  # dados = pd.read_csv("/content/drive/MyDrive/Colab Notebooks/sheets/extratoNovadaxIR2021.csv", sep=';', decimal='.')
  dados = pd.read_csv(dir+arqIn, sep=';', decimal='.')
  #editar nome coluna
  col =['History', 'Tipo', 'Moeda', 'QTDE', 'Saldo_unitario',
        'Status']
  dados.columns = col
  dados.columns = pd.Series(dados.columns).str.upper() 
  return dados

######

def filtra_dados(dados):
  dados = dados.query("TIPO not in ['Taxa de transação', 'Bônus', 'Depósito em Reais', 'Taxa de saque em Reais', 'Saque em Reais', 'Taxa de saque de criptomoedas', 'Saque de criptomoedas']")
  dados = dados.query("MOEDA in ['SOL', 'BTC', 'GALA', 'ETH', 'ADA', 'BCH', 'XMR']")
  return dados

######

def trata_colunas(dados):
  std1 = '[+|-]\d{1,2},\d{0,8}'
  std2 = 'compra|venda|investimento'
  std3 = '\d{2}/\d{2}/\d{4}'
  std4 = '[R$]{2}\d{1,2}\w[.]?\d{0,2}'
  padrao1 = re.compile(std1, flags=re.IGNORECASE)
  padrao2 = re.compile(std2, flags=re.IGNORECASE)
  padrao3 = re.compile(std3)
  padrao4 = re.compile(std4)

  lSaldo = [padrao4.findall(i) for i in dados['QTDE'] if (padrao4.search(i))]

  #tratamento de virg campo VALOR.
  list_saldo_compra = []
  for i in lSaldo:
    for el in i:   
      list_saldo_compra.append(float(str(el).replace("R$", "")))
  dados['CUSTO_OPERACAO'] = list_saldo_compra

  #tratamento coluna QTDE
  achou = [padrao1.findall(i) for i in dados['QTDE'] if (padrao1.search(i))] 

  #tratamento de virg campo VALOR.
  nlist = []
  for i in achou:
    for el in i:   
      nlist.append(float(str(el).replace(",", ".")))
  dados['QTDE'] = nlist 

  #tratamento coluna TIPO 
  lTipo = [(padrao2.findall(i)) for i in dados['TIPO']]
  lTipo2 = [str(ind2).replace("['", "").replace("']", "").lower() for ind2 in [ind1 for ind1 in lTipo ]]
  dados['TIPO'] = lTipo2

  #tratar investimento > 0 como compra, e < 0 como venda
  col_tipo = []
  for i in range(len(dados['QTDE'])):
    vitem = dados.iloc[i]
    vtipo = vitem['TIPO']
    vqtde = vitem['QTDE']
    if vqtde < 0:
      #atualiza TIPO para venda
      vtipo = 'venda'
      col_tipo.append(vtipo)
    elif  vqtde > 0:
      #atualiza TIPO para compra
      vtipo = 'compra'
      col_tipo.append(vtipo)
  dados['TIPO'] = col_tipo
  #coluna COTACAO
  list_cotacao =[]
  list_cotacao = dados['CUSTO_OPERACAO']/dados['QTDE'].abs()
  dados['COTACAO'] = list_cotacao

  #coluna SALDO_UNITARIO
  saldoapos = [float((i.replace(',','.'))) for i in dados['SALDO_UNITARIO']]
  dados['SALDO_UNITARIO'] = saldoapos
  ##########
  dados['SALDO_REAIS'] = dados['SALDO_UNITARIO']*dados['COTACAO']
  dados = dados[::-1]
  dados.reset_index(drop=True, inplace=True)

  #tratamento coluna HISTORY
  achou_data = [(padrao3.findall(i)) for i in dados['HISTORY']]
  lTipo3 = [str(ind2).replace("['", "").replace("']", "").lower() for ind2 in [ind1 for ind1 in achou_data ]]
  dados['HISTORY'] = lTipo3

  return dados

######

def calcula_preco_medio(dados):
  #CALCULO DO PRECO MEDIO    
  moedas = dados['MOEDA'].unique().tolist()
  #calcular PM
  global dic
  dic = dict()

  for moeda in moedas:
    dfMoeda = dados.query(f"MOEDA in ['{moeda}']")
    vsaldo_qtde = 0
    pm = 0
    preco_medio = []
    for i in range(len(dfMoeda)):

      vitem = dfMoeda.iloc[i] 
      vtipo = vitem['TIPO']
      vqtde = vitem['QTDE']
      vsaldo_apos = vitem['SALDO_REAIS']

      vsaldo_qtde = vsaldo_qtde + vqtde

      if vtipo == 'compra':
        pm = vsaldo_apos / vsaldo_qtde
        preco_medio.append(pm)

      elif vtipo == 'venda':
        preco_medio.append(pm)

      #print(f' {vhistory} || {vmoeda}\t||{vtipo}    \t||{vqtde}   \t||{vsaldo_qtde}\t||{pm}')

    dfMoeda['PRECO_MEDIO'] = preco_medio
    dic[moeda] = dfMoeda
  dfResult = pd.DataFrame()
  for v in dic.values():
    dfResult = pd.concat([v, dfResult])

  dfResult.sort_index(inplace=True)
  return dfResult

######

def calcula_lucro(dados):
  #calculo do lucro/prejuizo =>> custo - (pm*qtde_vend)
  moedas = dados['MOEDA'].unique().tolist()

  for moeda in moedas:
    dfMoeda = dados.query(f"MOEDA in ['{moeda}']")

    lista_lucro_prejuizo = []
    for i in range(len(dfMoeda)):

      vitem = dfMoeda.iloc[i]
      vqtde = vitem['QTDE']
      vcusto = vitem['CUSTO_OPERACAO']
      vpm = vitem['PRECO_MEDIO']
      vtipo = vitem['TIPO']

      if vtipo == 'venda':
        lucro_prejuizo = (vcusto - (vpm*(-vqtde)))  
        lista_lucro_prejuizo.append(lucro_prejuizo)
        #print(f'tipo: {vtipo} lucro: {lucro_prejuizo}')

      elif vtipo == 'compra':
        lista_lucro_prejuizo.append(0)
        #print(f'tipo compra: {vtipo} lucro: {lucro_prejuizo}')
        len(lista_lucro_prejuizo)
    dfMoeda['LUCRO/PREJUIZO'] = lista_lucro_prejuizo

    dic[moeda] = dfMoeda
  dfFinal = pd.DataFrame()
  for v in dic.values():
    dfFinal = pd.concat([v, dfFinal])

  dfFinal.sort_index(inplace=True)  
  return dfFinal

######

def calcula_posicao_final(dados):
  #calculo posição e lucro final

  dfLucro_posicao = pd.DataFrame(columns=('DATA', 'MOEDA', 'POSICAO_UNIT', 'POSICAO_REAIS', 'PRECO_MEDIO', 'LUCRO/PREJUIZO'))

  moedas = dados['MOEDA'].unique().tolist()
  for moeda in moedas:
    dfMoeda = dados.query(f"MOEDA in ['{moeda}']")

    lista_lucro_prejuizo = []
    for i in range(len(dfMoeda)):
      vitem = dfMoeda.iloc[i]
      vdata = vitem['HISTORY']
      vmoeda = vitem['MOEDA']
      vsaldo_Uni = vitem['SALDO_UNITARIO']
      vsaldo_reais = vitem['SALDO_REAIS']
      vpm = vitem['PRECO_MEDIO']
      vlucro = vitem['LUCRO/PREJUIZO']
      vtipo = vitem['TIPO']
      # print(f'meu item {vitem}')
      dicDados = dicDados + vitem
    # print(dicDados)
    #print(f'{vdata},  {vmoeda}, {vsaldo_Uni}, {vsaldo_reais}, {vpm},  {vlucro}, {vtipo}')
    #dfLucro_posicao.loc[:,(dfLucro_posicao.columns)] = pd.DataFrame([(vdata, vmoeda, vsaldo_Uni, vsaldo_reais, vpm, vlucro)])
    #dfLucro_posicao = pd.DataFrame([(vdata, vmoeda, vsaldo_Uni, vsaldo_reais, vpm, vlucro)])
    #dfLucro_posicao = pd.concat(vdata, vmoeda, vsaldo_Uni, vsaldo_reais, vpm, vlucro, dfLucro_posicao)
  return dados

###################MAIN
dir = os.path.dirname(os.path.abspath(__file__))
arqIn = '/extratoNovadaxIR2021.csv'
arqOut = '/ResultadoCriptoIR2021.csv'

dados1 = leitura()

dados = filtra_dados(dados1)
dados = trata_colunas(dados)
dados = calcula_preco_medio(dados)
dados = calcula_lucro(dados)
# dados = calcula_posicao_final(dados)
print(dados)

dados.to_csv(dir+arqOut, sep=';', decimal=',', index=False)
