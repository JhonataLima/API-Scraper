import requests
from bs4 import BeautifulSoup
import pandas as pd
from unidecode import unidecode
from fastapi import FastAPI, HTTPException
from typing import Dict, List

class WebScraper:
    def __init__(self, base_url, years):
        """
        Inicializa a instância do WebScraper.
        
        :param base_url: URL base da página web que será acessada.
        :param years: Lista de anos para os quais os dados serão coletados.
        """
        self.base_url = base_url
        self.years = years
        self.data = pd.DataFrame()

    def get_html_content(self, url, parameters):
        """
        Faz uma solicitação HTTP GET para o URL fornecido e retorna o conteúdo HTML.
        
        :param url: URL para onde a solicitação será enviada.
        :param parameters: Parâmetros da solicitação HTTP.
        :return: Conteúdo HTML da resposta.
        """
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        return response.content

    def parse_html(self, html_content):
        """
        Analisa o conteúdo HTML e retorna um objeto BeautifulSoup.
        
        :param html_content: Conteúdo HTML da página.
        :return: Objeto BeautifulSoup para análise do HTML.
        """
        return BeautifulSoup(html_content, 'html.parser')

    def find_data_table(self, soup):
        """
        Encontra e retorna a tabela de dados na página HTML analisada.
        
        :param soup: Objeto BeautifulSoup com o HTML da página.
        :return: Tabela de dados encontrada.
        """
        return soup.find('table', class_='tb_base tb_dados')

    def extract_table_data(self, table, classification_button=''):
        """
        Extrai os dados da tabela e retorna um DataFrame.
        
        :param table: Tabela HTML da qual os dados serão extraídos.
        :param classification_button: (Opcional) Valor para adicionar na coluna de classificação.
        :return: DataFrame com os dados extraídos da tabela.
        """
        headers = [header.text.strip() for header in table.find_all('th')]
        headers.append('Classification')
        if classification_button:
            headers.append('Button')

        current_classification = ''
        second_last_item = ''
        rows = []

        footer = table.find('tfoot', class_='tb_total')

        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]

            if footer and row in footer.find_all('tr'):
                row_data.append('Total')
            elif 'tb_item' in cells[0].get('class', []):
                current_classification = row_data[0]
                second_last_item = current_classification
                row_data.append(current_classification)
            elif 'tb_subitem' in cells[0].get('class', []):
                row_data.append(second_last_item)
            else:
                row_data.append('')

            if classification_button:
                row_data.append(classification_button)
            rows.append(row_data)
        return pd.DataFrame(rows, columns=headers)

    def run_scraping(self):
        """
        Executa o processo de coleta de dados para todos os anos e botões especificados.
        """
        for year in self.years:
            button_iterable = self.get_buttons()
            if button_iterable:
                for button in button_iterable:
                    params = self.create_parameters(year, button)
                    html_content = self.get_html_content(self.base_url, params)
                    soup = self.parse_html(html_content)
                    table = self.find_data_table(soup)
                    if table:
                        df = self.extract_table_data(table, button['classification_button'])
                        df['Year'] = year
                        self.data = pd.concat([self.data, df], ignore_index=True)
                    else:
                        print(f'Table not found for year {year} and button {button["value"]}.')
            else:
                params = self.create_parameters(year)
                html_content = self.get_html_content(self.base_url, params)
                soup = self.parse_html(html_content)
                table = self.find_data_table(soup)
                if table:
                    df = self.extract_table_data(table)
                    df['Year'] = year
                    self.data = pd.concat([self.data, df], ignore_index=True)
                else:
                    print(f'Table not found for year {year}.')

        self.clean_data()

    def create_parameters(self, year, button=None):
        """
        Cria os parâmetros da solicitação HTTP para um ano e botão específicos.
        
        :param year: Ano para o qual os dados são solicitados.
        :param button: (Opcional) Botão para incluir nos parâmetros.
        :return: Parâmetros da solicitação HTTP.
        """
        raise NotImplementedError

    def get_buttons(self):
        """
        Obtém a lista de botões (ou outras opções) para a navegação na página web.
        
        :return: Lista de botões ou opções.
        """
        raise NotImplementedError
    
    def clean_data(self):
        """
        Limpa e normaliza os dados do DataFrame, removendo acentos e caracteres especiais.
        """
        def normalize_text(text):
            """
            Remove acentos e caracteres especiais e converte o texto para maiusculas.
            
            :param text: Texto a ser normalizado.
            :return: Texto normalizado.
            """
            if isinstance(text, str):
                if text.strip() == "-" or text.strip() == "*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        for column in self.data.select_dtypes(include='object'):
            self.data[column] = self.data[column].map(normalize_text)


class SiteExportacaoScraper(WebScraper):
    def __init__(self, anos=range(2020, 2024), botao=None):
        url = 'http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_06'  # Definindo a URL como um atributo de classe
        self.csv_url = ['http://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ExpEspumantes.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ExpUva.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ExpSuco.csv']
        self.tipo = 'Exp'
        super().__init__(url, anos)
        self.botao = botao

    def get_params(self, ano, botao=None):
        params = {'ano': ano}
        if botao:
            params[botao['name']] = botao['value']
        return params
    
    def transform_dados(self):
        super().transform_dados()  # Chama o método da classe base para as transformações comuns
    
        # Remover acentuação e caracteres especiais e converter para maiúsculas
        def normalize_text(text):
            if isinstance(text, str):
                if text.strip() == "-" or text.strip()=="*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        # Aplicar normalização a todas as colunas de texto
        for col in self.dados.select_dtypes(include='object'):
            self.dados[col] = self.dados[col].map(normalize_text)

        # Renomear a coluna 'Quantidade (Kg)' para 'Quantidade'
        self.dados = self.dados.rename(columns={'Quantidade (Kg)': 'Quantidade'})

        # Garantir que todos os valores na coluna 'Quantidade' sejam strings antes de remover os pontos
        self.dados['Quantidade'] = self.dados['Quantidade'].astype(str).str.replace('.', '')
        
        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Quantidade'] = pd.to_numeric(self.dados['Quantidade'], errors='coerce').fillna(0).astype(int)

        # Garantir que todos os valores na coluna 'Valor (US$)' sejam strings antes de remover os pontos
        self.dados['Valor (US$)'] = self.dados['Valor (US$)'].astype(str).str.replace('.', '')

        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Valor (US$)'] = pd.to_numeric(self.dados['Valor (US$)'], errors='coerce').fillna(0).astype(int)


        # Ordenar as colunas
        colunas = ['Países', 'Ano', 'Quantidade', 'Valor (US$)', 'Botao']
        self.dados = self.dados[colunas]

        # Remover as linhas que possuem o total do ano no Web Scraping
        self.dados = self.dados.loc[(self.dados['Países'] != 'TOTAL') | (self.dados['Países'] != 'TOTAL')]
        #self.dados = self.dados.drop(columns='Classificação')
    
    def run(self):
        super().run()  # Chama o método run da classe base
        self.transform_dados()  # Aplica as transformações nos dados

    def get_botoes(self):
        if self.botao:
            return [self.botao]
        else:
            return [
                {'name': 'subopcao', 'value': 'subopt_01', 'classificacao_botao': 'VINHOS DE MESA'},
                {'name': 'subopcao', 'value': 'subopt_02', 'classificacao_botao': 'ESPUMANTES'},
                {'name': 'subopcao', 'value': 'subopt_03', 'classificacao_botao': 'UVAS FRESCAS'},
                {'name': 'subopcao', 'value': 'subopt_04', 'classificacao_botao': 'SUCO DE UVA'}
            ]


class SiteImportacaoScraper(WebScraper):
    def __init__(self, anos=range(2020, 2024), botao=None):
        url = 'http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_05'  # Definindo a URL como um atributo de classe
        self.csv_url = ['http://vitibrasil.cnpuv.embrapa.br/download/ImpVinhos.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ImpEspumantes.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ImpFrescas.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ImpPassas.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ImpSuco.csv']
        self.tipo = 'Imp'
        super().__init__(url, anos)
        self.botao = botao

    def get_params(self, ano, botao=None):
        params = {'ano': ano}
        if botao:
            params[botao['name']] = botao['value']
        return params
    
    def transform_dados(self):
        super().transform_dados()  # Chama o método da classe base para as transformações comuns
    
        # Remover acentuação e caracteres especiais e converter para maiúsculas
        def normalize_text(text):
            if isinstance(text, str):
                if text.strip() == "-" or text.strip()=="*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        # Aplicar normalização a todas as colunas de texto
        for col in self.dados.select_dtypes(include='object'):
            self.dados[col] = self.dados[col].map(normalize_text)

        # Renomear a coluna 'Quantidade (Kg)' para 'Quantidade'
        self.dados = self.dados.rename(columns={'Quantidade (Kg)': 'Quantidade'})

        # Garantir que todos os valores na coluna 'Quantidade' sejam strings antes de remover os pontos
        self.dados['Quantidade'] = self.dados['Quantidade'].astype(str).str.replace('.', '')

        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Quantidade'] = pd.to_numeric(self.dados['Quantidade'], errors='coerce').fillna(0).astype(int)

        # Garantir que todos os valores na coluna 'Valor (US$)' sejam strings antes de remover os pontos
        self.dados['Valor (US$)'] = self.dados['Valor (US$)'].astype(str).str.replace('.', '')

        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Valor (US$)'] = pd.to_numeric(self.dados['Valor (US$)'], errors='coerce').fillna(0).astype(int)


        # Ordenar as colunas
        colunas = ['Países', 'Ano', 'Quantidade', 'Valor (US$)', 'Botao']
        self.dados = self.dados[colunas]

        # Remover as linhas que possuem o total do ano no Web Scraping
        self.dados = self.dados.loc[(self.dados['Países'] != 'TOTAL') | (self.dados['Países'] != 'TOTAL')]
        
    
    def run(self):
        super().run()  # Chama o método run da classe base
        self.transform_dados()  # Aplica as transformações nos dados

    def get_botoes(self):
        if self.botao:
            return [self.botao]
        else:
            return [
                {'name': 'subopcao', 'value': 'subopt_01', 'classificacao_botao': 'VINHOS DE MESA'},
                {'name': 'subopcao', 'value': 'subopt_02', 'classificacao_botao': 'ESPUMANTES'},
                {'name': 'subopcao', 'value': 'subopt_03', 'classificacao_botao': 'UVAS FRESCAS'},
                {'name': 'subopcao', 'value': 'subopt_04', 'classificacao_botao': 'UVAS PASSAS'},
                {'name': 'subopcao', 'value': 'subopt_05', 'classificacao_botao': 'SUCO DE UVA'}
            ]


class SiteProcessamentoScraper(WebScraper):
    def __init__(self, anos=range(2020, 2024), botao=None):
        url = 'http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_03'  # Definindo a URL como um atributo de classe
        self.csv_url = ['http://vitibrasil.cnpuv.embrapa.br/download/ProcessaViniferas.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ProcessaAmericanas.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ProcessaMesa.csv',
                        'http://vitibrasil.cnpuv.embrapa.br/download/ProcessaSemclass.csv']
        self.tipo = 'Proces'
        super().__init__(url, anos)
        self.botao = botao

    def get_params(self, ano, botao=None):
        params = {'ano': ano}
        if botao:
            params[botao['name']] = botao['value']
        return params

    def transform_dados(self):
        super().transform_dados()  # Chama o método da classe base para as transformações comuns

        # Verificar se a coluna 'Cultivar' existe, caso contrário criar e preencher com 'Classificação' - Caso do botão SEM CLASSIFICAÇÃO
        if 'Cultivar' not in self.dados.columns and 'Classificação' in self.dados.columns:
            self.dados['Cultivar'] = self.dados['Classificação']

        # Verificar se a coluna 'Sem definição' existe no DataFrame
        if 'Sem definição' in self.dados.columns:
            if 'Cultivar' in self.dados.columns:
                # Substituir os valores na coluna 'Cultivar' pelos valores da coluna 'Sem definição'
                mask = self.dados['Sem definição'].notna() & self.dados['Cultivar'].isna()
                self.dados.loc[mask, 'Cultivar'] = self.dados.loc[mask, 'Sem definição']
            # Removendo a coluna 'Sem definição' que aparece apenas no botão SEM CLASSIFICAÇÃO do Processamento, pois não tem a coluna 'Cultivar'
            self.dados.drop(columns=['Sem definição'], inplace=True)

        # Remover acentuação e caracteres especiais e converter para maiúsculas
        def normalize_text(text):
            if isinstance(text, str):
                if text.strip() == "-" or text.strip()=="*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        # Aplicar normalização a todas as colunas de texto
        for col in self.dados.select_dtypes(include='object'):
            self.dados[col] = self.dados[col].map(normalize_text)

        # Renomear a coluna 'Quantidade (Kg)' para 'Quantidade'
        self.dados = self.dados.rename(columns={'Quantidade (Kg)': 'Quantidade'})

        # Garantir que todos os valores na coluna 'Quantidade' sejam strings antes de remover os pontos
        self.dados['Quantidade'] = self.dados['Quantidade'].astype(str).str.replace('.', '')
        
        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Quantidade'] = pd.to_numeric(self.dados['Quantidade'], errors='coerce').fillna(0).astype(int)
        
        # Ordenar as colunas
        colunas = ['Cultivar', 'Classificação', 'Ano', 'Quantidade', 'Botao']
        self.dados = self.dados[colunas]

        # Remover as linhas que possuem o total do ano no Web Scraping
        self.dados = self.dados.loc[(self.dados['Cultivar'] != 'TOTAL') | (self.dados['Classificação'] != 'TOTAL')]
    
    def run(self):
        super().run()  # Chama o método run da classe base
        self.transform_dados()  # Aplica as transformações nos dados

    def get_botoes(self):
        if self.botao:
            return [self.botao]
        else:
            return [
                {'name': 'subopcao', 'value': 'subopt_01', 'classificacao_botao': 'VINIFERAS'},
                {'name': 'subopcao', 'value': 'subopt_02', 'classificacao_botao': 'AMERICANAS E HIBRIDAS'},
                {'name': 'subopcao', 'value': 'subopt_03', 'classificacao_botao': 'UVAS DE MESA'},
                {'name': 'subopcao', 'value': 'subopt_04', 'classificacao_botao': 'SEM CLASSIFICACAO'}
            ]


class SiteProducaoScraper(WebScraper):
    def __init__(self, anos=range(2020, 2023), botao=None):
        url = 'http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_02'  # Definindo a URL como um atributo de classe
        self.csv_url = ['http://vitibrasil.cnpuv.embrapa.br/download/Producao.csv']
        self.tipo = 'Prod'
        super().__init__(url, anos)
        self.botao = botao
    
    def get_params(self, ano, botao=None):
        return {'ano': ano}

    def get_botoes(self):
        return []
    
    def transform_dados(self):
        # Remover acentuação e caracteres especiais e converter para maiúsculas
        def normalize_text(text):
            if isinstance(text, str):
                if text.strip() == "-" or text.strip()=="*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        # Aplicar normalização a todas as colunas de texto
        for col in self.dados.select_dtypes(include='object'):
            self.dados[col] = self.dados[col].map(normalize_text)

        # Renomear a coluna 'Quantidade (L.)' para 'Quantidade'
        self.dados = self.dados.rename(columns={'Quantidade (L.)': 'Quantidade'})

        # Garantir que todos os valores na coluna 'Quantidade' sejam strings antes de remover os pontos
        self.dados['Quantidade'] = self.dados['Quantidade'].astype(str).str.replace('.', '')

        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Quantidade'] = pd.to_numeric(self.dados['Quantidade'], errors='coerce').fillna(0).astype(int)

        # Ordenar as colunas
        colunas = ['Produto', 'Classificação', 'Ano', 'Quantidade']
        self.dados = self.dados[colunas]

        # Remover as linhas que possuem o total do ano no Web Scraping
        self.dados = self.dados.loc[(self.dados['Produto'] != 'TOTAL') | (self.dados['Classificação'] != 'TOTAL')]

    def run(self):
        super().run()  # Chama o método run da classe base
        self.transform_dados()  # Aplica as transformações nos dados
    

class SiteComercializacaoScraper(WebScraper):
    def __init__(self, anos=range(2020, 2024), botao=None):
        url = 'http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_04'  # Definindo a URL como um atributo de classe
        self.csv_url = ['http://vitibrasil.cnpuv.embrapa.br/download/Comercio.csv']
        self.tipo = 'Comerc' # tipo do site Comercio
        super().__init__(url, anos)
        self.botao = botao

    def get_params(self, ano, botao=None):
        return {'ano': ano}

    def get_botoes(self):
        return []
    
    def transform_dados(self):
        # Remover acentuação e caracteres especiais e converter para maiúsculas
        def normalize_text(text):
            if isinstance(text, str):
                if text.strip() == "-" or text.strip()=="*":
                    return "0"
                else:
                    return unidecode(text).upper()
            else:
                return text

        # Aplicar normalização a todas as colunas de texto
        for col in self.dados.select_dtypes(include='object'):
            self.dados[col] = self.dados[col].map(normalize_text)

        # Renomear a coluna 'Quantidade (L.)' para 'Quantidade'
        self.dados = self.dados.rename(columns={'Quantidade (L.)': 'Quantidade'})

        # Garantir que todos os valores na coluna 'Quantidade' sejam strings antes de remover os pontos
        self.dados['Quantidade'] = self.dados['Quantidade'].astype(str).str.replace('.', '')
        
        # Substituir valores não numéricos por zero antes de converter para inteiro
        self.dados['Quantidade'] = pd.to_numeric(self.dados['Quantidade'], errors='coerce').fillna(0).astype(int)


        # Ordenar as colunas
        colunas = ['Produto', 'Classificação', 'Ano', 'Quantidade']
        self.dados = self.dados[colunas]

        # Remover as linhas que possuem o total do ano no Web Scraping
        self.dados = self.dados.loc[(self.dados['Produto'] != 'TOTAL') | (self.dados['Classificação'] != 'TOTAL')]
    

    def run(self):
        super().run()  # Chama o método run da classe base
        self.transform_dados()  # Aplica as transformações nos dados


# Metadados da API para descrever as tags
tags_metadata = [
    {
        "name": "Produção",
        "description": "Endpoints relacionados à produção de vinhos, sucos e derivados do Rio Grande do Sul",
    },
    {
        "name": "Processamento",
        "description": "Endpoints relacionados à quantidade de uvas processadas no Rio Grande do Sul",
    },
    {
        "name": "Comercialização",
        "description": "Endpoints relacionados à comercialização de vinhos e derivados no Rio Grande do Sul",
    },
    {
        "name": "Importação",
        "description": "Endpoints relacionados à importação de derivados de uva",
    },
    {
        "name": "Exportação",
        "description": "Endpoints relacionados à exportação de derivados de uva",
    },
    {   
        "name": "Página Inicial",
        "description": "Bem-vindo à API da Vitivinicultura",
    }
]

# Criação da instância da aplicação FastAPI
app = FastAPI(
    title="API de Captura: Dados de Vinhos",
    description="API para retornar dados disponíveis no site (http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_01).",
    version="0.0.1",
    openapi_tags=tags_metadata,
)

# Endpoint para a página inicial
@app.get("/", response_model=Dict[str, str], tags=["Página Inicial"], summary="Página Inicial", description="Página Inicial")
def root():
    """
    Endpoint para a página inicial da API.
    Retorna uma mensagem de boas-vindas.
    """
    return {"message": "Essa é a página inicial do app"}

# Endpoint para obter dados de produção
@app.get("/producoes", response_model=Dict[str, str], tags=["Produção"], summary="Obter dados de produção", description="Retorna dados de produção de vinhos, sucos e derivados")
def get_producoes(): 
    # parametro a ser preenchido para execucao do scraper
    # anos: List[int] = [2020, 2021, 2022, 2023]
    """
    Endpoint para obter dados relacionados à produção de vinhos, sucos e derivados.
    Retorna dados fictícios para demonstração.
    """
    # try:
    #     data = SiteProducaoScraper(anos=anos)
    #     data.run()
    #     # Converter o campo 'Ano' para string
    #     for item in data:
    #         item['Ano'] = str(item['Ano'])
    #     return data.dados.to_dict(orient='records')
    # except:
    #     raise HTTPException(status_code=500, detail=str(e))
    
    data={
        "Ano": "2023",
        "Tipo": "Vinho",
        "Quantidade": "1000 litros"
    }
    return data

# Endpoint para obter dados de processamento
@app.get("/processamentos", response_model=Dict[str, str], tags=["Processamento"], summary="Obter dados de processamento", description="Retorna dados sobre a quantidade de uvas processadas")
def get_processamentos():
    # parametro a ser preenchido para execucao do scraper
    # anos: List[int] = [2020, 2021, 2022, 2023]
    """
    Endpoint para obter dados relacionados ao processamento de uvas.
    Retorna dados fictícios para demonstração.
    """
    # try:
    #     data = SiteProcessamentoScraper(anos=anos)
    #     data.run()
    #     # Converter o campo 'Ano' para string
    #     for item in data:
    #         item['Ano'] = str(item['Ano'])
    #     return data.dados.to_dict(orient='records')
    # except:
    #     raise HTTPException(status_code=500, detail=str(e))
    data = {
        "Ano": "2023",
        "Tipo": "Uvas",
        "Quantidade": "500 toneladas"
    }
    return data

# Endpoint para obter dados de comercialização
@app.get("/comercializacoes", response_model=Dict[str, str], tags=["Comercialização"], summary="Obter dados de comercialização", description="Retorna dados sobre a comercialização de vinhos e derivados")
def get_comercializacoes():
    # parametro a ser preenchido para execucao do scraper
    # anos: List[int] = [2020, 2021, 2022, 2023]
    """
    Endpoint para obter dados relacionados à comercialização de vinhos e derivados.
    Retorna dados fictícios para demonstração.
    """
    # try:
    #     data = SiteComercializacaoScraper(anos=anos)
    #     data.run()
    #     # Converter o campo 'Ano' para string
    #     for item in data:
    #         item['Ano'] = str(item['Ano'])
    #     return data.dados.to_dict(orient='records')
    # except:
    #     raise HTTPException(status_code=500, detail=str(e))
    data = {
        "Ano": "2023",
        "Produto": "Vinho",
        "Valor": "20000 USD"
    }
    return data

# Endpoint para obter dados de importação
@app.get("/importacoes", response_model=Dict[str, str], tags=["Importação"], summary="Obter dados de importação", description="Retorna dados sobre a importação de derivados de uva")
def get_importacoes():
    # parametro a ser preenchido para execucao do scraper
    # anos: List[int] = [2020, 2021, 2022, 2023]
    """
    Endpoint para obter dados relacionados à importação de derivados de uva.
    Retorna dados fictícios para demonstração.
    """
    # try:
    #     data = SiteImportacaoScraper(anos=anos)
    #     data.run()
    #     # Converter o campo 'Ano' para string
    #     for item in data:
    #         item['Ano'] = str(item['Ano'])
    #     return data.dados.to_dict(orient='records')
    # except:
    #     raise HTTPException(status_code=500, detail=str(e))
    data = {
        "Ano": "2023",
        "Produto": "Suco de Uva",
        "Quantidade": "3000 litros"
    }
    return data

# Endpoint para obter dados de exportação
@app.get("/exportacoes", response_model=Dict[str, str], tags=["Exportação"], summary="Obter dados de exportação", description="Retorna dados sobre a exportação de derivados de uva")
def get_exportacoes():
    # parametro a ser preenchido para execucao do scraper
    # anos: List[int] = [2020, 2021, 2022, 2023]
    """
    Endpoint para obter dados relacionados à exportação de derivados de uva.
    Retorna dados fictícios para demonstração.
    """
    # try:
    #     data = SiteExportacaoScraper(anos=anos)
    #     data.run()
    #     # Converter o campo 'Ano' para string
    #     for item in data:
    #         item['Ano'] = str(item['Ano'])
    #     return data.dados.to_dict(orient='records')
    # except:
    #     raise HTTPException(status_code=500, detail=str(e))
    data = {
        "Ano": "2023",
        "Produto": "Vinho",
        "Quantidade": "2000 litros"
    }
    return data

# Execução da aplicação FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
