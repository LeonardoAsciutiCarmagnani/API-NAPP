import datetime
import json
import os
import re
import sys
from pymongo import MongoClient, errors
from dotenv import load_dotenv
from datetime import datetime, timedelta
from api import Napp
from logger_config import basic_setup_logger

# Carrega as variáveis do .env
load_dotenv()

# Define o caminho para o arquivo initial_load.txt
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'initial_load.txt')

logger = basic_setup_logger()
logger.info("Logger configurado com sucesso.")

def is_valid_cnpj(cnpj):
    return bool(re.match(r'^\d{14}$', cnpj))

def save_json(json_data):
    logger.info("Salvando JSON...")
    try:
        # Define o diretório e garante que a pasta 'result' exista
        result_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'result')
        os.makedirs(result_directory, exist_ok=True)  # Cria a pasta 'result' se não existir

        # Obtém a data e hora atual para usar no nome do arquivo
        timestamp = datetime.now().strftime('%d%m%Y-%H%M%S')
        result_filename = f'result_{timestamp}.json'
        result_path = os.path.join(result_directory, result_filename)

        # Salva o JSON no caminho especificado com formatação
        with open(result_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)  # Usa json.dump para formatar o JSON com indentação

        logger.info(f"JSON salvo com sucesso em: {result_path}")

        # Chamada para a API após salvar o JSON
        Napp.fetchAPI()
        
    except Exception as e:
        logger.critical(f"Erro ao salvar o arquivo JSON: {e}")

def defineDate():
    
        logger.info("Definindo periodo de busca (ultimos 15 dias)")
        start = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d 00:00:00")
        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return start, end

def flowMongo():
    cnpj_loja = os.getenv('CNPJ_LOJA')
    
    if not cnpj_loja:
        logger.error("Configure o CNPJ antes de iniciar o script!")
        sys.exit(1)
    
    if not is_valid_cnpj(cnpj_loja):
        logger.error("Erro: O CNPJ da loja deve ter exatamente 14 digitos e não pode conter pontuacao.")
        sys.exit(1)

    logger.info(f"CNPJ da loja encontrado: {cnpj_loja}")

    try:
        logger.info("Tentando conexao com a instancia MongoDB...")
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['cplug_offline']
        collection = db['sales']
        client.admin.command('ping')
        logger.info("Conexao realizada com sucesso")
    except errors.ConnectionFailure as e:
        logger.critical(f"Falha ao conectar ao MongoDB: {e}")
        return
    except errors.ServerSelectionTimeoutError as e:
        logger.critical(f"Tentativas para conexao esgotadas! {e}")
        return
    except Exception as e:
        logger.critical(f"Ocorreu um erro inesperado: {e}")
        return
    
    start_date, end_date = defineDate()
    logger.info(f"Periodo definido: {start_date} - {end_date}")
    
    # Pipeline de agregação para consulta 
    pipeline = [
        {
            '$match': {
                'sale': True,
                'fiscal_status': { '$in': ['PENDING', 'TRANSMITTED'] },
                'payments': {
                    '$elemMatch': {
                        'payment_method': { '$in': ['Cartão de Crédito','Cartão de Débito'] }
                    }
                },
                'createdAt': {
                    '$gte': start_date, 
                    '$lte': end_date 
                }
            }
        },
        {
            '$project': { 
                '_ID': '$unique_id',
                '_DataHora': '$sale_end',
                '_Valor': { '$multiply': ['$total_value', 1.0] },
                '_Cancelado': {
                    '$cond': [
                        { '$eq': ['$deletedAt', None] },
                        'N',
                        'S'
                    ]
                },
                '_Tipo_Operacao': { '$literal': 1 }
            }
        },
        {
            '$group': {
                '_id': '$_ID',
                'DataHora': { '$first': '$_DataHora' },
                'Valor': { '$first': '$_Valor' },
                'Cancelado': { '$first': '$_Cancelado' },
                'Tipo_Operacao': { '$first': '$_Tipo_Operacao' }
            }
        },
        {
            '$project': {
                '_id': 0,
                'ID': '$_id',
                'DataHora': 1,
                'Valor': 1,
                'Cancelado': 1,
                'Tipo_Operacao': 1
            }
        }
    ]
    
    try:
        logger.info("Realizando consulta...")
        results = collection.aggregate(pipeline)
        logger.info("Transformando resultados...")
        result_list = list(results)
    except errors.PyMongoError as e:
        logger.error(f"Erro ao consultar dados: {e}")
        sys.exit(1)
    
    logger.info("Inserindo CNPJ da loja...")
    for item in result_list:
        if 'Valor' in item:
            item['Valor'] = "{:.2f}".format(item['Valor']).replace('.', ',')
        item['CNPJ'] = cnpj_loja
    
    logger.info("Ordenando a lista...")
    result_list = [
        {
            'ID': item.get('ID'),
            'DataHora': item.get('DataHora'),
            'Valor': item.get('Valor'),
            'Cancelado': item.get('Cancelado'),
            'Tipo_Operacao': item.get('Tipo_Operacao'),
            'CNPJ': cnpj_loja
        }
        for item in result_list
    ]
    
    logger.info("Salvando JSON...")
    save_json(result_list)

def main():
    flowMongo()

if __name__ == "__main__":
    main()
