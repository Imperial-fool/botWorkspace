
#Email libs
import smtplib, ssl,random
import imaplib, email
from email.header import decode_header
import time

port = 465
password = ""
cont = ssl.create_default_context()

def checkin(profit:float, t:float, buys, sells,account_value):
    print("checking")
    
    j = round((time.time() - t)/60,2)
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=cont) as server:
        server.login("botmanupdate@gmail.com", password)
        sender_email = "botmanupdate@gmail.com"
        receiver_email = ""
        message = """\
        Subject: Bot Update

        """
        line = randomsaying()
        message += line
        message += ("Profit: " + str(profit)+"\n")
        message += ("Time since start(min):" + str(j)+"\n")
        message += ("Value of account in btc: "+ str(account_value.value) +"\n")
        message += ("Number of Trades: " + str(buys+sells))
        
        server.sendmail(sender_email,receiver_email,message)
    server.quit
def error_report(line,line2=""):
   try:
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=cont) as server:
        server.login("botmanupdate@gmail.com", password)
        sender_email = "botmanupdate@gmail.com"
        receiver_email = ""
        message = """\
        Subject: Bot Error

        """
        message += line
        if len(line2) > 0: 
            message += line2

        server.sendmail(sender_email,receiver_email,message)
    server.quit
   except Exception as e:
       print(e)
def custom_message(line):
   try:
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=cont) as server:
        server.login("botmanupdate@gmail.com", password)
        sender_email = "botmanupdate@gmail.com"
        receiver_email = ""
        message = """\
        Subject: Message

        """
        message += line
       

        server.sendmail(sender_email,receiver_email,message)
    server.quit
   except Exception as e:
       print(e)
def randomsaying():
    random.seed(a=None,version=2)
    random_number = random.randint(1,5)
    if random_number == 1:
        return "The Oracles have breached the aether!\n Heed their message\n"
    if random_number == 2:
        return "Ah yes here are your stats\n"
    if random_number == 3:
        return "I AM STILL ALIVE\n"
    if random_number == 4:
        return "We have breached the great shroud!\n"
    if random_number == 5:
        return "Here is your arcane wisdom\n"
def emailcontroller(checkin,shutdown,restart, buy_sell_arr,print_items):
    
    
    while True:
        with imaplib.IMAP4_SSL("imap.gmail.com",993) as imap:
            imap.login("botmanupdate@gmail.com", password)
            status, messages = imap.select("Commands")

            N = 2

            messages = int(messages[0])
            for i in range(messages, messages-N, -1):
                try:
                 res, msg = imap.fetch(str(i), "(RFC822)")
                except Exception as e:
                    print(e)
                    continue
                for response in msg:
                    if isinstance(response, tuple):
                            # parse a bytes email into a message object
                        msg = email.message_from_bytes(response[1])

                        From, encoding = decode_header(msg.get("From"))[0]
                        if isinstance(From, bytes):
                            From = From.decode(encoding)
                            # if the email message is multipart
                        if From == "":
                             
                             if msg.is_multipart():
                # iterate over email parts
                                for part in msg.walk():
                    # extract content type of email
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    
                                    try:
                                        # get the email body
                                        body = part.get_payload(decode=True).decode()
                                    except:
                                        pass
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        if body == "Hello":
                                            print("Hello")
                                            custom_message("Greetings")
                                        if body == "Update":
                                            checkin.value = 1
                                            custom_message("Update will be summoned...\nPlease Wait")
                                        if body == "Shutdown":
                                            custom_message("If you wish...")
                                            shutdown.value = 1
                                        if body == "Restart":
                                            custom_message("What have I done, to deserve a reboot?")
                                            restart.value = 1
                                        if body == "Help":
                                            custom_message("And Help you shall recieve!\n Possible commands:\n Hello, sends greetings \n Update, pushes checkin message \n Shutdown, shuts down program \n Restart, kills then restarts processes \n Buy, will set a buy per for item \n Sell, will sell item \n Pairs, will send list of pairs active")
                                        if "Buy" in body:
                                            if len(body) < 10:
                                             for j,i in enumerate(body):
                                                buy_sell_arr[j] = i.encode()
                                            
                                            print(buy_sell_arr)
                                            print(buy_sell_arr.value)
                                            custom_message("Will Attempt Buy")
                                        if "Sell" in body:
                                            if len(body) < 10:
                                             for j,i in enumerate(body):
                                                buy_sell_arr[j] = i.encode()
                                            
                                            custom_message("Will Attempt Sell")
                                        if "Pairs" in body:
                                            print_items.value = 1
                                            custom_message("Pairs incoming: ")


                                        
            clean(imap)                              
            imap.expunge()
            imap.close()
            imap.logout()
            time.sleep(360)
def clean(imap):
    typ, data = imap.search(None, 'ALL')
    for num in data[0].split():
        imap.store(num, '+FLAGS', '\\Deleted')
