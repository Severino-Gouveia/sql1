import pyodbc
import pandas as pd
from flask import Flask, render_template, send_from_directory, request
from datetime import date, timedelta

app = Flask(__name__)

# Configurações de conexão com o banco de dados
SERVIDOR = '172.20.20.38'
BANCO_DE_DADOS = 'EAMPROD'
USUARIO = 'excel'
SENHA = 'excel'
NOME_DO_DRIVER = 'ODBC Driver 17 for SQL Server'

# String de conexão formatada
string_de_conexao = f'DRIVER={{{NOME_DO_DRIVER}}};SERVER={SERVIDOR};DATABASE={BANCO_DE_DADOS};UID={USUARIO};PWD={SENHA}'

def consultar_banco(consulta_sql, *params):
    try:
        with pyodbc.connect(string_de_conexao) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(consulta_sql, *params)
                registros = cursor.fetchall()
                df = pd.DataFrame.from_records(registros, columns=[desc[0] for desc in cursor.description])

                # Restante do código permanece inalterado
                df['Hora'] = df['DATA_TEXTO'].dt.strftime('%H:%M:%S')
                df['Semana'] = df['DATA_TEXTO'].dt.strftime('%U')
                df['Data'] = df['DATA_TEXTO'].dt.strftime('%d/%m/%Y')

                return df

    except pyodbc.Error as erro:
        print(f"Erro: {erro}")
        return None

def construir_consulta_sql(data_inicial, data_final, departamento):
    return '''
        SELECT 
            R5ADDETAILS.ADD_CREATED as DATA_TEXTO, 
            R5ADDETAILS.ADD_CODE as AES,
            R5EVENTS.EVT_DESC as Descricao, 
            CASE R5EVENTS.EVT_STATUS
                WHEN 'FE' THEN 'Fechado'
                WHEN 'RP' THEN 'Reprogramar'
                WHEN 'CM' THEN 'Aguardando Chegada Material'
                WHEN 'P' THEN 'Programada'
                WHEN 'REJ' THEN 'Rejeitada'
                WHEN 'AP' THEN 'Aprovada'
                WHEN 'PM' THEN 'Aguardar Parada de Maquina'
                WHEN 'R' THEN 'Emitido'
                WHEN 'CL' THEN 'Concluida'
                WHEN 'EE' THEN 'Em Execucao'
                ELSE 'OUTROS'
            END as Status,
            CASE R5ADDETAILS.ADD_TYPE
                WHEN '*' THEN 'Sim'
                ELSE 'Nao'
            END as Observacao,
            R5EVENTS.EVT_STATUS as EVT_STAT, 
            R5ADDETAILS.ADD_LINE as Linha,
            R5ADDETAILS.ADD_TEXT as Observacoes, 
            R5ADDETAILS.ADD_USER as matricula,
            R5PERSONNEL.PER_DESC as Colaborador, 
            R5CREWS.CRW_DESC AS turno,
            R5EVENTS.EVT_MRC AS Departamento
        FROM 
            EAMPROD.dbo.R5ADDETAILS R5ADDETAILS
            INNER JOIN R5EVENTS ON R5EVENTS.EVT_CODE = R5ADDETAILS.ADD_CODE
            INNER JOIN R5PERSONNEL ON R5PERSONNEL.PER_CODE = R5ADDETAILS.ADD_USER
            INNER JOIN R5CREWEMPLOYEES ON R5CREWEMPLOYEES.CRE_PERSON = R5ADDETAILS.ADD_USER
            INNER JOIN R5CREWS ON R5CREWEMPLOYEES.CRE_CREW = R5CREWS.CRW_CODE
        WHERE 
            R5ADDETAILS.ADD_ENTITY = 'EVNT' 
            AND (R5ADDETAILS.ADD_CREATED >= ?) 
            AND (R5ADDETAILS.ADD_CREATED < ?) 
            AND (R5EVENTS.EVT_MRC = ?);
    '''

# Rota para servir arquivos estáticos, incluindo imagens
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Rota para renderizar a página HTML com o filtro por departamento
@app.route('/filtrar/<departamento>')
def filtrar_departamento(departamento):
    data_inicial = date.today() - timedelta(days=1)
    data_final = date.today()

    consulta_sql = construir_consulta_sql(data_inicial, data_final, departamento)

    df = consultar_banco(consulta_sql, data_inicial, data_final, departamento)

    if df is not None:
        # Select only the desired columns for the RDM
        relatorio_estilizado = df[['AES', 'Descricao', 'Colaborador', 'Observacoes', 'Hora', 'Status', 'Semana', 'Data', 'Departamento']]
        imagem_path = 'img/ASSINATURA_2024_GPTW.png'
        return render_template('index.html', data=relatorio_estilizado.to_dict('records'), imagem_path=imagem_path)
    else:
        return "Erro na consulta do banco de dados."

# Rota para renderizar a página HTML com filtro por data
@app.route('/filtrar/data', methods=['POST'])
def filtrar_data():
    data_inicial = request.form['data_inicial']
    data_final = request.form['data_final']
    departamento = request.form.get('departamento', default=None)

    # Se o departamento não foi especificado, defina um valor padrão
    if departamento is None:
        departamento = 'DP02'

    # Converta as datas para o formato desejado
    data_inicial = pd.to_datetime(data_inicial).date()
    data_final = pd.to_datetime(data_final).date() + timedelta(days=1)

    consulta_sql = construir_consulta_sql(data_inicial, data_final, departamento)

    df = consultar_banco(consulta_sql, data_inicial, data_final, departamento)

    if df is not None:
        # Restante do código permanece inalterado
        relatorio_estilizado = df[['AES', 'Descricao', 'Colaborador', 'Observacoes', 'Hora', 'Status', 'Semana', 'Data', 'Departamento']]
        imagem_path = 'img/ASSINATURA_2024_GPTW.png'
        return render_template('index.html', data=relatorio_estilizado.to_dict('records'), imagem_path=imagem_path)
    else:
        return "Erro na consulta do banco de dados."


# Rota para renderizar a página HTML sem filtro
@app.route('/')
def index():
    return filtrar_departamento('DP01')  # Defina o departamento padrão aqui

# Remova esta parte se estiver usando o aplicativo Flask em um ambiente de produção
if __name__ == '__main__':
    app.run(debug=True)

    
