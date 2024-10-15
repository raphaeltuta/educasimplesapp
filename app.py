from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from werkzeug.utils import secure_filename

# Configuração do app
app = Flask(__name__)
app.secret_key = 'seu_segredo_aqui'

# Configuração do upload de arquivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria diretório de uploads, se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Base de dados temporária
usuarios = []
publicacoes = []
postagens = []

admin_credenciais = {
    'username': 'Raphael',
    'password': '12345678900'
}

# Rotas
@app.route('/')
def index():
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('password')
        for usuario in usuarios:
            if usuario['email'] == email and usuario['senha'] == senha:
                session['usuario'] = usuario['nome']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
        flash('Email ou senha incorretos!', 'error')
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('name')
        email = request.form.get('email')
        senha = request.form.get('password')
        confirmar_senha = request.form.get('confirm-password')

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('cadastro'))

        usuario_id = len(usuarios)
        usuarios.append({'id': usuario_id, 'nome': nome, 'email': email, 'senha': senha})
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' in session:
        return render_template('dashboard.html', usuario=session['usuario'])
    else:
        flash('Por favor, faça login para acessar o Dashboard.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/professores')
def professores():
    if 'usuario' in session:
        return render_template('professores.html')
    else:
        return redirect(url_for('login'))

# Rotas de Admin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == admin_credenciais['username'] and password == admin_credenciais['password']:
            session['admin'] = True
            flash('Login de administrador realizado com sucesso!', 'success')
            return redirect(url_for('admin'))

        flash('Credenciais de administrador incorretas!', 'error')
        return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if 'admin' in session:
        search_query = request.args.get('search')
        usuarios_filtrados = [u for u in usuarios if search_query.lower() in u['email'].lower()] if search_query else usuarios
        return render_template('admin.html', usuarios=usuarios_filtrados, publicacoes=publicacoes)
    else:
        flash('Você precisa fazer login como administrador.', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash('Você foi desconectado como administrador!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/publicar', methods=['POST'])
def publicar():
    if 'admin' not in session:
        flash('Acesso negado. Apenas administradores podem publicar materiais.', 'error')
        return redirect(url_for('admin_login'))

    area = request.form.get('area')
    titulo = request.form.get('titulo')
    descricao = request.form.get('descricao')
    arquivo = request.files['arquivo']
    
    if not area or not titulo or not descricao:
        flash('Todos os campos são obrigatórios!', 'error')
        return redirect(url_for('admin'))

    if arquivo:
        arquivo_nome = secure_filename(arquivo.filename)
        arquivo_path = os.path.join(app.config['UPLOAD_FOLDER'], arquivo_nome)
        arquivo.save(arquivo_path)

        banner = request.files.get('banner')
        banner_nome = None
        if banner and banner.filename != '':
            banner_nome = secure_filename(banner.filename)
            banner_path = os.path.join(app.config['UPLOAD_FOLDER'], banner_nome)
            banner.save(banner_path)

        publicacao = {'area': area, 'titulo': titulo, 'descricao': descricao, 'arquivo': arquivo_nome, 'banner': banner_nome}
        publicacoes.append(publicacao)

        flash('Material publicado com sucesso!', 'success')
    else:
        flash('Arquivo não enviado!', 'error')

    return redirect(url_for('admin'))

@app.route('/materiais')
def materiais():
    if 'usuario' in session:
        return render_template('materiais.html', usuario=session['usuario'], materiais=publicacoes)
    else:
        flash('Você precisa estar logado para acessar os materiais.', 'error')
        return redirect(url_for('login'))

# Fórum
@app.route('/forum')
def forum():
    if 'usuario' in session:
        return render_template('forum.html', postagens=postagens, usuario=session['usuario'])
    else:
        flash('Você precisa estar logado para acessar o fórum.', 'error')
        return redirect(url_for('login'))

@app.route('/forum/nova_postagem', methods=['GET', 'POST'])
def nova_postagem():
    if 'usuario' in session:
        if request.method == 'POST':
            titulo = request.form.get('titulo')
            descricao = request.form.get('descricao')

            postagem_id = len(postagens)
            postagens.append({'id': postagem_id, 'titulo': titulo, 'descricao': descricao, 'comentarios': []})
            flash('Postagem criada com sucesso!', 'success')
            return redirect(url_for('forum'))

        return render_template('nova_postagem.html', usuario=session['usuario'])
    else:
        flash('Você precisa estar logado para adicionar postagens.', 'error')
        return redirect(url_for('login'))

@app.route('/forum/postagem/<int:postagem_id>', methods=['GET', 'POST'])
def visualizar_postagem(postagem_id):
    if 'usuario' in session:
        if postagem_id < len(postagens):
            postagem = postagens[postagem_id]
            if request.method == 'POST':
                comentario = request.form.get('comentario')
                postagem['comentarios'].append({'usuario': session['usuario'], 'comentario': comentario})
                flash('Comentário adicionado com sucesso!', 'success')
                return redirect(url_for('visualizar_postagem', postagem_id=postagem_id))

            return render_template('visualizar_postagem.html', postagem=postagem, usuario=session['usuario'])
        else:
            flash('Postagem não encontrada!', 'error')
            return redirect(url_for('forum'))
    else:
        flash('Você precisa estar logado para visualizar postagens.', 'error')
        return redirect(url_for('login'))

# Doações
@app.route('/doacao')
def doacao():
    return render_template('doacao.html')

if __name__ == '__main__':
    app.run(debug=True)
