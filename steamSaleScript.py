import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime

class PricePredictor:

    def __init__ (self,appId,targetPrice=None):
        self.appId=appId
        self.targetPrice=targetPrice
        self.storeAPI=f"https://store.steampowered.com/api/appdetails?appids={appId}&cc=us"


    def getGameInfo(self):
        try:
            response = requests.get(self.storeAPI)
            data = response.json()
            
            if not data[str(self.appId)]['success']:
                return None
            
            gameData = data[str(self.appId)]['data']
            priceInfo = gameData.get('price_overview', {})
            
            return {
                'name': gameData['name'],
                'is_free': gameData.get('is_free', False),
                'price': priceInfo.get('final', 0) / 100,  # Convert cents to dollars
                'original_price': priceInfo.get('initial', 0) / 100,
                'discount_percent': priceInfo.get('discount_percent', 0),
                'on_sale': priceInfo.get('discount_percent', 0) > 0
            }
        except Exception as e:
            print(f"Error fetching game info: {e}")
            return None

    def sendEmail(self,gameInfo,emailConfig):

        try:
            msg=MIMEMultipart()
            msg['from']=emailConfig['from_email']
            msg['to']=emailConfig['to_email']
            msg['subject']=f"{gameInfo['name']} is on sale"


            body = f"""
            Great news! {gameInfo['name']} is now on sale on Steam!
            
            Original Price: ${gameInfo['original_price']:.2f}
            Sale Price: ${gameInfo['price']:.2f}
            Discount: {gameInfo['discount_percent']}% OFF
            
            Check it out: https://store.steampowered.com/app/{self.appId}
            
            Happy gaming! 🎮
            """


            msg.attach(MIMEMultipart(body,'plain'))

            with smtplib.SMTP('smpt.gamil.com',587) as server:
                server.starttls()
                server.login(emailConfig['from_email'], emailConfig['password'])
                server.send_message(msg)

            print(f"Email sent suceessfuly")
            return True
        except Exception as e:
            print(f"error sending email{e}")
            return False
    
    def sendSMS_via_Email(self,gameInfo,smsConfig):

        carriers={
            'verizon':'vtext.com',
            'tmobile': 'tmomail.net',
            'att': 'txt.att.net',
            'sprint': 'messaging.sprintpcs.com',
            'boost': 'smsmyboostmobile.com',
            'cellcom':'sms.cellcom.com'
        }

        try:
            carrierDomain =carriers.get(smsConfig['carrier'].lower())

            if not carrierDomain:
                print(f"{carrierDomain} is not supported at this time")
                return None

            toAddress=f"{gameInfo['phone_number']}@{carrierDomain}"

            msg=MIMEText(f"{gameInfo['name']} is {gameInfo['discount%']}% off! Now ${gameInfo['price']:.2f}")
            msg['From']=smsConfig['from_email']
            msg['To']=toAddress

            print(f"SMS Sent Successfully")
            return True
        except Exception as e:
            print("Error sending sms{e}")
            return None
        

    def check_Notify(self,notiConfig):
        
        
        gameInfo=self.getGameInfo()

        if not gameInfo:
            print("Game information was not found")
            return 
        
        print(f"\n📊 {gameInfo['name']}")
        print(f"Current Price: ${gameInfo['price']:.2f}")
        print(f"On Sale: {'Yes' if gameInfo['on_sale'] else 'No'}")


        notify=False


        if gameInfo['on_sale']:
            if self.targetPrice is None:
                notify=True
            elif gameInfo['price'] <= self.targetPrice:
                should_notify = True
        if should_notify:
            print(f"🎉 Sale detected! Sending notifications...")
            
            if notiConfig.get('email'):
                self.sendEmail(gameInfo, notiConfig['email'])   
            if notiConfig.get('sms'):
                self.sendSMS_via_Email(gameInfo, notiConfig['sms'])
        else:
            print("No sale or price not low enough yet")


from config import EMAILCONFIG, SMSCONFIG 
if __name__=="__main__":
        steamAppID="1151340"
        TARGETPRICE="39.99"


        NOTI_CONFIG={
            'email':EMAILCONFIG,
            'sms':SMSCONFIG
        }


        monitor = PricePredictor(steamAppID, TARGETPRICE)
        monitor.check_Notify(NOTI_CONFIG)



        
        
    
