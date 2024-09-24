import smtplib
import email.message
   
def sendEmailForCriticalErrors(bodyText):
    bodyEmail = bodyText
    
    msg = email.message.Message()
    msg['Subject'] = "REPORT AUTOMÁTICO DE ERROS - SCRIPT NAPP"
    msg['From'] = f'lasciuti@multipoint.com.br'
    msg['To'] = 'suporten1@multipoint.com.br'
    password = 'Frederico100#'
    
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(bodyEmail)
    
    s = smtplib.SMTP('smtp.office365.com: 587')
    s.starttls()
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
    