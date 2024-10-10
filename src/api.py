from datetime import datetime
import json
import os
import requests
from dotenv import load_dotenv
from time import sleep
from logger_config import api_setup_logger
from send_email import sendEmailForCriticalErrors

class Napp:
    
    api_logger = api_setup_logger()
    
    def __init__(self):
        load_dotenv()
        self.user = os.getenv('NAPP_USR')
        self.psw = os.getenv('NAPP_PSW')
        self.token = None
        self.result_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'result')
        
    def get_latest_json(self):
        try:
            json_files = [
                f for f in os.listdir(self.result_directory) 
                if f.endswith('.json') and os.path.isfile(os.path.join(self.result_directory, f))
            ]
            
            if not json_files:
                raise FileNotFoundError("Nenhum arquivo JSON encontrado no diretório 'result'.")
            
            # Ordena os arquivos pelo timestamp no nome do arquivo
            json_files.sort(key=lambda x: datetime.strptime(x.split('_')[1].split('.')[0], '%d%m%Y-%H%M%S'))
            latest_file = json_files[-1]  
            latest_file_path = os.path.join(self.result_directory, latest_file)
            return latest_file_path
        
        except FileNotFoundError as e:
            self.api_logger.error(str(e))
            return None
        except Exception as e:
            self.api_logger.error(f"Erro ao obter o arquivo JSON mais recente: {str(e)}")
            return None
    
    def get_token(self):
        if not self.user or not self.psw:
            self.api_logger.critical("Usuário ou senha não encontrados nas variaveis de ambiente")
            raise SystemExit()
        try:
            self.api_logger.info("Requisitando token")
            url = 'https://publisher.nappsolutions.com/auth'
            headers = {'content-type': 'application/json'}
            payload = {
                'username': self.user,
                'password': self.psw
            }
            res = requests.post(url=url, data=json.dumps(payload), headers=headers)
            if res.status_code == 200:
                self.token = res.json().get("token")
                self.api_logger.info("Token obtido com sucesso")
                self.api_logger.info(self.token) 
            else:
                self.api_logger.error("Falha ao requisitar token: " + {str(res.json())})
                sendEmailForCriticalErrors(f"Falha ao requisitar token com a NAPP ({os.getenv('ALIAS')})")
                raise SystemExit()
        except Exception as error:
            self.api_logger.critical("Erro ao requisitar token: " + {str(error)})
            sendEmailForCriticalErrors(f"Falha do tipo Expection ao requisitar token ({os.getenv('ALIAS')}): {str(error)}")
            raise SystemExit()

    def upload(self, file_path):
        try:
            if not file_path:
                self.api_logger.error("Nenhum arquivo JSON fornecido para fazer upload.")
                return
            if not os.path.isfile(file_path):
                self.api_logger.error(f"Arquivo não encontrado: {file_path}")
                return
            if os.path.getsize(file_path) == 0:
                self.api_logger.error("O arquivo JSON está vazio.")
                return

            self.api_logger.info(f"Iniciando upload do arquivo: {file_path}")
            url = 'https://publisher.nappsolutions.com/receiver'
            headers = {'Authorization': self.token, 'Content-Type': 'application/json'}

            # Ler o conteúdo do arquivo JSON
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            for attempt in range(3): 
                try:
                    res = requests.post(url=url, headers=headers, json=json_data, timeout=30)
                    
                    if res.status_code == 200:
                        self.api_logger.info("JSON enviado com sucesso")
                        break
                    else:
                        self.api_logger.error("Falha ao enviar arquivo, tentando novamente... Tentativa %d: %s", attempt + 1, str(res.json()))
                        sleep(5)
                except requests.RequestException as e:
                    self.api_logger.error(f"Erro na requisição de upload: {str(e)}")
                    sleep(5)
            else:
                self.api_logger.critical("Falhas consecutivas ao tentar enviar o arquivo.")
                sendEmailForCriticalErrors(f"Falhas consecutivas ao tentar enviar o arquivo para NAPP ({os.getenv('ALIAS')}")
        except Exception as ex:
            self.api_logger.critical("Erro ao enviar arquivo: %s", str(ex))
            sendEmailForCriticalErrors(f"Houve um erro CRÍTICO do tipo Exception e não foi possível enviar o JSON ({os.getenv('ALIAS')}): {ex}")
            self.api_logger.info('Finalizando execução')
            exit()
        
        
    def fetchAPI():       
        api_client = Napp()
        api_client.get_token()
        latest_file = api_client.get_latest_json()
        if latest_file:
            api_client.upload(latest_file)
        else:
            api_client.api_logger.error("Nenhum arquivo JSON para enviar")
       
