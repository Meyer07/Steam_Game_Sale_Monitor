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
            msg['To']=emailConfig['to_email']
            msg['subject']=f"{gameInfo['name']} is on sale"


            body = f"""
            Great news! {gameInfo['name']} is now on sale on Steam!
            
            Original Price: ${gameInfo['original_price']:.2f}
            Sale Price: ${gameInfo['price']:.2f}
            Discount: {gameInfo['discount_percent']}% OFF
            
            Check it out: https://store.steampowered.com/app/{self.appId}
            
            Happy gaming! 🎮
            """


            msg.attach(MIMEText(body,'plain'))

            with smtplib.SMTP('mail.twc.com',587) as server:
                server.starttls()
                server.login(emailConfig['from_email'], emailConfig['password'])
                server.send_message(msg)

            print(f"Email sent sucessfully")
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
            'cellcom':'smscellcom.com'
        }

        try:
            carrierDomain =carriers.get(smsConfig['carrier'].lower())

            if not carrierDomain:
                print(f"{carrierDomain} is not supported at this time")
                return None

            toAddress=f"{smsConfig['phone_number']}@{carrierDomain}"

            msg=MIMEText(f"{gameInfo['name']} is {gameInfo['discount_percent']}% off! Now ${gameInfo['price']:.2f}")
            msg['From']=smsConfig['from_email']
            msg['To']=toAddress

            with smtplib.SMTP('mail.twc.com',587) as server:
                server.starttls()
                server.login(smsConfig['from_email'], smsConfig['password'])
                server.send_message(msg)
            print(f"SMS Sent Successfully")
            return True
        except Exception as e:
            print(f"Error sending sms: {e}")
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
                notify = True
        if notify:
            print(f"🎉 Sale detected! Sending notifications...")
            
            if notiConfig.get('email'):
                self.sendEmail(gameInfo, notiConfig['email'])   
            if notiConfig.get('sms'):
                self.sendSMS_via_Email(gameInfo, notiConfig['sms'])
        else:
            print("No sale or price not low enough yet")

def sendWishlistNotif(sales,NOTI_CONFIG):
        try:
            body = "🎮 Great news! Games from your Steam wishlist are on sale!\n\n"
        
            for game in sales:
                body += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                body += f"🎯 {game['name']}\n"
                body += f"   Original: ${game['original_price']:.2f}\n"
                body += f"   Sale Price: ${game['price']:.2f}\n"
                body += f"   Discount: {game['discount_percent']}% OFF\n"
                body += f"   Link: https://store.steampowered.com/app/{game.get('app_id', '')}\n\n"
        
            body += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            body += f"Total games on sale: {len(sales)}\n"
            body += "\nHappy gaming! 🎮"
        
            if NOTI_CONFIG.get('email'):
                msg = MIMEMultipart()
                msg['From'] = NOTI_CONFIG['email']['from_email']
                msg['To'] = NOTI_CONFIG['email']['to_email']
                msg['Subject'] = f"🎮 {len(sales)} Game{'s' if len(sales) > 1 else ''} from Your Wishlist On Sale!"
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP('mail.twc.com', 587) as server:
                server.starttls()
                server.login(NOTI_CONFIG['email']['from_email'],NOTI_CONFIG['email']['password'])
                server.send_message(msg)
            
            print(f"✅ Email notification sent with {len(sales)} game(s)!")

            if NOTI_CONFIG.get('sms'):
                sms_body = f"{len(sales)} wishlist game(s) on sale! Check your email for details."
            
                carriers = {
                    'verizon': 'vtext.com',
                    'tmobile': 'tmomail.net',
                    'att': 'txt.att.net',
                    'cellcom': 'sms.cellcom.com'
            }
            
                carrier_domain = carriers.get(NOTI_CONFIG['sms']['carrier'].lower())
                if carrier_domain:
                    to_address = f"{NOTI_CONFIG['sms']['phone_number']}@{carrier_domain}"
                
                    sms_msg = MIMEText(sms_body)
                    sms_msg['From'] = NOTI_CONFIG['sms']['from_email']
                    sms_msg['To'] = to_address
                
                    with smtplib.SMTP('mail.twc', 587) as server:
                        server.starttls()
                        server.login(NOTI_CONFIG['sms']['from_email'],NOTI_CONFIG['sms']['password'])
                        server.send_message(sms_msg)
                
                print(f"✅ SMS notification sent!")
        
        except Exception as e:
            print(f"❌ Error sending wishlist notification: {e}")
            return
def checkWishList(wishlist, NOTI_CONFIG, targetPrice=None):
    
        salesFound = []
        print(f"\n{'='*60}")
        print(f"🎮 Checking {len(wishlist)} games on your wishlist...")  
        print(f"{'='*60}\n")

        for appId in wishlist:  
            monitor = PricePredictor(appId, targetPrice)  
            gameInfo = monitor.getGameInfo()  

            if not gameInfo:
                print(f"⚠️  Could not fetch info for App ID: {appId}")
                continue
            
        print(f"📊 {gameInfo['name']}")
        print(f"   Price: ${gameInfo['price']:.2f}")
        print(f"   On Sale: {'✅ Yes' if gameInfo['on_sale'] else '❌ No'}")    

        notify = False  
        if gameInfo['on_sale']:
            if targetPrice is None:
                notify = True  
            elif gameInfo['price'] <= targetPrice:
                notify = True  
    
        if notify:
            gameInfo['app_id'] = appId 
            salesFound.append(gameInfo)
            print(f"   🎉 SALE DETECTED! {gameInfo['discount_percent']}% off!")
        
        print()  # Blank line between games

       
        if salesFound:  # Check if list is not empty
            sendWishlistNotif(salesFound,NOTI_CONFIG)
        else:
            print("\n😔 No sales found on your wishlist right now.")

        return salesFound
    

from config import EMAILCONFIG, SMSCONFIG 
if __name__=="__main__":
        wishList=[
            "1174180",
            "1151340",
            "2362050",
            "1817070",
            "2651280",
            "1817190",
            "381210",
            "729040",
            "2183900"
        ]

        TARGETPRICE=None


        NOTI_CONFIG={
            'email':EMAILCONFIG,
            'sms':SMSCONFIG
        }

        checkWishList(wishList, NOTI_CONFIG, TARGETPRICE)

        


        
        
    
