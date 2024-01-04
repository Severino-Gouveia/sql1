import os
import pyodbc
import pandas as pd
from openpyxl import Workbook
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# Configurações de conexão com o banco de dados
SERVIDOR = '172.20.20.38'
BANCO_DE_DADOS = 'EAMPROD'
USUARIO = 'excel'
SENHA = 'excel'
NOME_DO_DRIVER = 'ODBC Driver 17 for SQL Server'

# String de conexão formatada
string_de_conexao = f'DRIVER={{{NOME_DO_DRIVER}}};SERVER={SERVIDOR};DATABASE={BANCO_DE_DADOS};UID={USUARIO};PWD={SENHA}'

# Função para criar o arquivo Excel e retornar o DataFrame
def criar_excel():
    try:
        with pyodbc.connect(string_de_conexao) as conexao:
            consulta_sql = '''
SELECT 
    R5ADDETAILS.ADD_CREATED as DATA_TEXTO, 
    R5ADDETAILS.ADD_CODE as AES,
    R5EVENTS.EVT_DESC as Descricão, 
    CASE R5EVENTS.EVT_STATUS
        WHEN 'FE' THEN 'Fechado'
        WHEN 'RP' THEN 'Reprogramar'
        WHEN 'CM' THEN 'Aguardando Chegada Material'
        WHEN 'P' THEN 'Programada'
        WHEN 'REJ' THEN 'Rejeitada'
        WHEN 'AP' THEN 'Aprovada'
        WHEN 'PM' THEN 'Aguardar Parada de Máquina'
        WHEN 'R' THEN 'Emitido'
        WHEN 'CL' THEN 'Concluída'
        WHEN 'EE' THEN 'Em Execução'
        ELSE 'OUTROS'
    END as Stat_AES,
    CASE R5ADDETAILS.ADD_TYPE
        WHEN '*' THEN 'Sim'
        ELSE 'Não'
    END as Observacao,
    R5EVENTS.EVT_STATUS as EVT_STAT, 
    R5ADDETAILS.ADD_LINE as Linha,
    R5ADDETAILS.ADD_TEXT as Observações, 
    R5ADDETAILS.ADD_USER as matricula,
    R5PERSONNEL.PER_DESC as Colaborador, 
    R5CREWS.CRW_DESC AS turno
FROM 
    EAMPROD.dbo.R5ADDETAILS R5ADDETAILS
    INNER JOIN R5EVENTS ON R5EVENTS.EVT_CODE = R5ADDETAILS.ADD_CODE
    INNER JOIN R5PERSONNEL ON R5PERSONNEL.PER_CODE = R5ADDETAILS.ADD_USER
    INNER JOIN R5CREWEMPLOYEES ON R5CREWEMPLOYEES.CRE_PERSON = R5ADDETAILS.ADD_USER
    INNER JOIN R5CREWS ON R5CREWEMPLOYEES.CRE_CREW = R5CREWS.CRW_CODE
WHERE 
    R5ADDETAILS.ADD_ENTITY = 'EVNT' 
    AND (R5ADDETAILS.ADD_CREATED >= DATEADD(DAY, DATEDIFF(DAY, 0, GETDATE()) - 1, 0)) 
    AND (R5ADDETAILS.ADD_CREATED < DATEADD(DAY, DATEDIFF(DAY, 0, GETDATE()), 0)) 
    AND (R5EVENTS.EVT_MRC ='DP02');

            '''

            with conexao.cursor() as cursor:
                cursor.execute(consulta_sql)
                registros = cursor.fetchall()
                df = pd.DataFrame.from_records(registros, columns=[desc[0] for desc in cursor.description])

                # Renomear a coluna 'Stat_AES' para 'Status'
                df.rename(columns={'Stat_AES': 'Status'}, inplace=True)

         
                # concerter formato de hora
                df['Hora'] = df['DATA_TEXTO'].dt.strftime('%H:%M:%S')

                # Selecão de variaveis
                relatorio_estilizado = df[['AES', 'Descricão', 'Colaborador', 'Observações', 'Hora', 'Status']]
                # Adicionar DataFrame data_texto
                relatorio_estilizado['Semana'] = df['DATA_TEXTO'].dt.strftime('%U')
                relatorio_estilizado['Data'] = df['DATA_TEXTO'].dt.strftime('%d/%m/%Y')


                # Verificar se o arquivo com o nome atual já existe
                contagem = 1
                while os.path.exists(f'static/RDM_{contagem}.xlsx'):
                    contagem += 1

                # Criar o nome do arquivo com a contagem
                excel_file = f'static/RDM_{contagem}.xlsx'

                # Salvar o arquivo estilizado
                relatorio_estilizado.to_excel(excel_file, index=False)

                print(f"Conclusão da criação {excel_file}.")

                return excel_file

    except pyodbc.Error as erro:
        print(f"Erro: {erro}")
        return None

# Rota para servir arquivos estáticos, incluindo imagens
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota para renderizar a página HTML
@app.route('/')
def index():
    excel_file = criar_excel()

    if excel_file:
        # Ler o arquivo Excel
        df = pd.read_excel(excel_file)

        # Caminho da imagem
        imagem_path = 'static/img/ASSINATURA_2024_GPTW.png'

        # Renderizar a página HTML, passando também o DataFrame
        return render_template('index.html', data=df, imagem_path=imagem_path)
    else:
        return "Erro na criação do relatório."

if __name__ == '__main__':
    app.run(debug=True)
