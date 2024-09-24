import smtplib
import email.message
from cryptography.fernet import Fernet

def load_key():
    return open("secret.key", "rb").read()

   
def sendEmailForCriticalErrors(bodyText):
    bodyEmail = bodyText
    
    msg = email.message.Message()
    msg['Subject'] = "REPORT AUTOMÁTICO DE ERROS - SCRIPT NAPP"
    msg['From'] = f'lasciuti@multipoint.com.br'
    msg['To'] = 'suporten1@multipoint.com.br'
    
    
    encrypted_password = b'gAAAAABm8r5igPGY9WMCl2QrL9mSRwC4nSWkH2VlwS3rjlzr9dLG1bxsiE87jeq2Rkg9wCUtytPcJD8-DWsV9K5tiKIssjF7Iw=='
    
    key = load_key()    
    cipher = Fernet(key)
    password = cipher.decrypt(encrypted_password).decode()
    
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(bodyEmail)
    
    s = smtplib.SMTP('smtp.office365.com: 587')
    s.starttls()
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
    