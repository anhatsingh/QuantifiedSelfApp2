from email.mime.base import MIMEBase
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_base64
import csv
from weasyprint import HTML
import uuid
import os

SMTP_SERVER_HOST = "localhost"
SMTP_SERVER_PORT = 1025

SMTP_SENDER_USERNAME = "QuantifiedApp@anhatsingh.com"
SMTP_SENDER_PASSWORD = ""

def send_mail(to, subject, message, attachments=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_SENDER_USERNAME
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        if attachments:
            with open(attachments, "rb") as file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
            encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachments}",
            )
            msg.attach(part)

        s = smtplib.SMTP(host=SMTP_SERVER_HOST, port=SMTP_SERVER_PORT)
        s.login(SMTP_SENDER_USERNAME, SMTP_SENDER_PASSWORD)

        s.send_message(msg)
        s.quit()
        return True
    except Exception as e:
        print(e)
        return False


def make_file(data, type):
    if type == "pdf":
        html = HTML(string=data)
        filename = "temp/" + str(uuid.uuid4()) + ".pdf"
        html.write_pdf(target=filename)
        return filename
    
    elif type == "csv":
        filename ="temp/" + str(uuid.uuid4()) + ".csv"
        f = open(filename, 'w')
        writer = csv.writer(f)

        for each_tracker in data:
            writer.writerow(["Tracker Details"])
            writer.writerow(["Name", each_tracker["tracker"]["name"]])
            writer.writerow(["Description", each_tracker["tracker"]["description"]])
            writer.writerow(["Type", each_tracker["tracker"]["type"]])
            writer.writerow(["", "", ""])

            if(each_tracker["tracker"]["type"] == "timerange"):
                writer.writerow(["TimeStamp", "Note", "Start Time", "End Time"])                
            else:
                writer.writerow(["TimeStamp", "Value", "Note"])                
            
            if(each_tracker["tracker"]["type"] == "timerange"):
                for i in each_tracker["logs"]:
                    writer.writerow([i["timestamp"], i["note"], i["start"], i["end"]])
            elif(each_tracker["tracker"]["type"] == "ms"):
                for i in each_tracker["logs"]:
                    writer.writerow([i["timestamp"], i["note"], ", ".join([x["value"] for x in i["value"]])])
            else:
                for i in each_tracker["logs"]:
                    writer.writerow([i["timestamp"], i["value"], i["note"]])
            writer.writerow(["", "", ""])
            writer.writerow(["", "", ""])
            writer.writerow(["", "", ""])
        f.close()
        return filename

def delete_file(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)