import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# Configurar o diretório estático para servir imagens
app.static_folder = 'static'
app.static_url_path = '/static'

# Função para criar o arquivo Excel e aplicar estilos
def criar_excel():
    # Criar um novo arquivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active

    # Escrever alguns dados de exemplo
    for row in range(1, 11):
        for col in range(1, 4):
            cell = ws.cell(row=row, column=col, value=f"Row {row}, Col {col}")

    # Salvar o arquivo Excel
    wb.save("static/excel.xlsx")

    # Informar ao usuário que o documento foi finalizado
    print("Documento finalizado.")

# Rota para servir arquivos estáticos, incluindo imagens
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Rota para renderizar a página HTML
@app.route('/')
def index():
    # Ler o arquivo Excel
    wb = openpyxl.load_workbook('static/excel.xlsx')
    ws = wb.active

    # Extrair dados do Excel
    data = []
    for row in ws.iter_rows(values_only=True):
        data.append(row)
    
    # Caminho da imagem
    imagem_path = 'static/img/ASSINATURA_2024_GPTW.png'
    
    # Renderizar a página HTML, passando também o caminho da imagem
    return render_template('index.html', data=data, imagem_path=imagem_path)

if __name__ == '__main__':
    # Chamar a função para criar o Excel antes de iniciar o servidor Flask
    criar_excel()

    # Iniciar o aplicativo Flask
    app.run(debug=True)

