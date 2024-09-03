# Plano de Deploy da API de Vitivinicultura

Este documento descreve o plano de deploy para a API de Vitivinicultura, utilizando Docker para simplificar o gerenciamento das dependências e configuração do ambiente.

## 1. Preparar o Ambiente de Desenvolvimento

### Estrutura do Projeto

Certifique-se de que todos os arquivos do projeto estão organizados de forma lógica. Sua estrutura de diretórios deve estar semelhante a:

```plaintext
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── routes.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── utils.py
│   │   ├── constants.py
│   │   ├── Scraper
│   │   │   ├── scraper_base.py
│   │   │   ├── site_producao.py
│   │   │   ├── site_processamento.py
│   │   │   ├── site_comercializacao.py
│   │   │   ├── site_importacao.py
│   │   │   ├── site_exportacao.py
│   │   └── CSV
│   │       ├── download_csv.py
│   │       ├── transform_csv.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
```

### Requisitos

Crie um arquivo `requirements.txt` para listar todas as dependências do projeto:

- FastAPI
- Uvicorn
- python-jose
- bcrypt
- Pydantic
- Pandas
- Requests
- BeautifulSoup4

Certifique-se de que o código está funcionando localmente sem erros.

## 2. Criar o Dockerfile

### Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto para definir a imagem Docker para a aplicação.

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore

Crie um arquivo `.dockerignore` para evitar que arquivos desnecessários sejam copiados para a imagem Docker.

```
__pycache__
*.pyc
*.pyo
.git
.venv
```

## 3. Construir e Testar a Imagem Docker

### Construir a Imagem

No terminal, navegue até a raiz do projeto e execute:

```bash
docker build -t vitivinicultura-api .
```

### Testar a Imagem Localmente

Execute a imagem criada para testar a API localmente:

```bash
docker run -p 8000:8000 vitivinicultura-api
```

Acesse `http://localhost:8000/docs` para verificar se a API está funcionando corretamente.

## 4. Configurar um Servidor Cloud

### Escolher um Provedor de Cloud

Escolha um provedor de serviços cloud, como AWS, DigitalOcean, Google Cloud, ou Azure.

### Configurar a Máquina Virtual

Crie uma nova instância de máquina virtual com uma distribuição Linux (como Ubuntu). Certifique-se de que a máquina virtual tem o Docker instalado.

### Acessar a Máquina Virtual

Use SSH para acessar a máquina virtual:

```bash
ssh your_user@your_server_ip
```

## 5. Implantar a API no Servidor

### Transferir os Arquivos do Projeto

Transfira os arquivos do projeto para o servidor. Você pode usar SCP, rsync, ou git:

```bash
scp -r /path/to/your/project your_user@your_server_ip:/path/to/deploy
```

### Construir a Imagem no Servidor

No servidor, navegue até o diretório onde os arquivos foram copiados e construa a imagem Docker:

```bash
cd /path/to/deploy
docker build -t vitivinicultura-api .
```

### Executar o Contêiner

Execute o contêiner Docker:

```bash
docker run -d -p 80:8000 vitivinicultura-api
```

## 6. Configurar um Proxy Reverso (Opcional)

### Instalar e Configurar o Nginx

Instale o Nginx no servidor:

```bash
sudo apt update
sudo apt install nginx
```

### Configurar o Nginx como Proxy Reverso

Edite o arquivo de configuração do Nginx (geralmente localizado em `/etc/nginx/sites-available/default`):

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Reinicie o Nginx para aplicar as configurações:

```bash
sudo systemctl restart nginx
```

## Conclusão

Seguindo esses passos, você terá sua API de Vitivinicultura implantada em um servidor cloud, utilizando Docker para gerenciamento de dependências e configuração do ambiente. Se precisar de mais ajuda, consulte a documentação oficial do Docker e do FastAPI.
