import json
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import sys
import re

def is_valid_cnpj(cnpj):
    # Verifica se o CNPJ contém apenas dígitos e possui exatamente 14 dígitos
    return bool(re.match(r'^\d{14}$', cnpj))

def main():
    # Conexão com o MongoDB
    try:
        print("Tentando conexão com instância MongoDB...")
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['cplug_offline']
        collection = db['sales']

        # Verifica se a conexão foi bem-sucedida
        client.admin.command('ping')
        print("Conexão realizada com sucesso")

    except errors.ConnectionFailure as e:
        print(f"Falha ao conectar ao MongoDB: {e}")
        sys.exit(1)

    except errors.ServerSelectionTimeoutError as e:
        print(f"Tentativas para conexão esgotadas! {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        sys.exit(1)

    # Pipeline de agregação de dados
    pipeline = [
        {
            '$match': {
            'sale': True,
            'fiscal_status': { '$in': ['PENDING', 'TRANSMITTED'] }
        },
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

    # Execute a consulta
    try:
        print("Realizando consulta...")
        results = collection.aggregate(pipeline)
    except errors.PyMongoError as e:
        print(f"Erro ao consultar o banco: {e}")
        sys.exit(1)


    print("Transformando resultados...")
    # Transformando os resultados em uma lista de dicionários
    result_list = list(results)

    print("Inserindo CNPJ da loja...")
    # Adiciona o CNPJ a cada item da lista
    for item in result_list:
        if 'Valor' in item:
            item['Valor'] = "{:.2f}".format(item['Valor']).replace('.', ',') # Trocando ponto para virgula e deixando 2 casas decimais no campo Valor
        item['CNPJ'] = cnpj_loja

    print("Ordenando a lista...")
    # Ordenação respectiva, que irá aparecer no JSON
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
    
    print("Convertendo para JSON...")
    # Converta a lista para JSON
    json_data = json.dumps(result_list, indent=4, default=str)

    print("Salvando JSON...")
    # Salvar em um arquivo ou usar o JSON diretamente
    with open('result.json', 'w') as json_file:
        json_file.write(json_data)
    print("JSON salvo com sucesso!")

if __name__ == '__main__':
    # Carrega as variáveis do .env
    load_dotenv()

    # Verificação: CNPJ_LOJA está presente no arquivo .env?
    cnpj_loja = os.getenv('CNPJ_LOJA')
    
    if not cnpj_loja:
        print("Configure o CNPJ antes de iniciar o script!")
        sys.exit(1)
    
    # Validação do CNPJ
    if not is_valid_cnpj(cnpj_loja):
        print("Erro: O CNPJ da loja deve ter exatamente 14 dígitos e não pode conter pontuação.")
        sys.exit(1)

    print(f"CNPJ da loja encontrado: {cnpj_loja}")
    main()  # Só executa o main() se o CNPJ estiver presente e for válido