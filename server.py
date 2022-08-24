from datetime import date
from queue import Empty
from tkinter import S
from cv2 import exp
import flask
import requests
import numpy
import json
import requests
import math
import websocket
import _thread
import time
import rel
import threading
s = requests.Session()
s.headers={"Content-Type":"application/json"}
tel_timer=-1
rakip_iha_verileri = ""
aiparam=[]

TelemetriVeriler = ""
lock_counter=0
qr_lock_counter=0
sihaKomut= '{"hedefLat":"0","hedefLon":"0"}'
takim_numarasi = 44
lock_start_data= {
                    "saat": 0,
                    "dakika": 0,
                    "saniye": 0,
                    "milisaniye": 0,
                    "otonom_kilitlenme": 0
            }
qr_lock_start_data= {
                    "saat": 0,
                    "dakika": 0,
                    "saniye": 0,
                    "milisaniye": 0,
                    "otonom_kilitlenme": 0
            }            

#hakem_url = "http://212.174.75.78"
hakem_url = "http://10.0.0.15:64559"

siha_ip = "http://192.168.31.40"  # 192.168.31.40
#siha_ip = "http://127.0.0.1"
auth_state = False
app = flask.Flask(__name__)
app.config["DEBUG"] = False

gidecekveri={"X": "0", "Y": "0", "yukseklik": "0", "genislik": "0", "tespit": "0", "emniyet": "0", "yertimer": "0"}

# sihadan gelen degsoz ===================================================
def degsoz_from_siha():
    global gidecekveri
    while True:
        try:
            kilitlenme = requests.get(
                    siha_ip+':6000/api/degsoz')
    
            gidecekveri=kilitlenme
        except:
            pass

# WEB SOCKET MISSION =======================================================

def ucaktan_veri_cekme(ws, message):  # missiondan çekilen veriler
   

    global TelemetriVeriler, rakip_iha_verileri, siha_ip,auth_state, gidecekveri,tel_timer

    telemetri = json.loads(message)
    kilitlenme_verisi = gidecekveri

    gps_zaman = str(telemetri['gpstime'])
    try:
        kilitlenme_json = kilitlenme_verisi
      
        is_uav_auto=0
        is_uav_locked=0
        if str(telemetri['mode'])=="AUTO" or str(telemetri['mode'])=="GUIDED" or str(telemetri['mode'])=="Auto" or str(telemetri['mode'])=="Guided":
             is_uav_auto=1
        else:
             is_uav_auto=0
        if str(kilitlenme_json["tespit"])=="1":
             is_uav_locked=1
        else:
             is_uav_locked=0    
        gps_zaman = str(telemetri['gpstime'])
        veri = {
            "takim_numarasi": int(2),
            "IHA_enlem": float(telemetri['lat']),
            "IHA_boylam": float(telemetri['lng']),
            "IHA_irtifa": float(telemetri['alt']),
            "IHA_dikilme": float(telemetri['pitch']),
            "IHA_yonelme": float(telemetri['yaw']),
            "IHA_yatis": float(telemetri['roll']),
            "IHA_hiz": float(telemetri['groundspeed']),
            "IHA_batarya": int(telemetri['battery_remaining']),
            "IHA_otonom": is_uav_auto,
            "IHA_kilitlenme": is_uav_locked,
            "Hedef_merkez_X": int(float(kilitlenme_json["X"])),
            "Hedef_merkez_Y": int(float(kilitlenme_json["Y"])),
            "Hedef_genislik": int(float(kilitlenme_json["yukseklik"])),
            "Hedef_yukseklik": int(float(kilitlenme_json["genislik"])),
            "GPSSaati": {
                "saat": gps_zaman[11:-11],
                "dakika": gps_zaman[14:-8],
                "saniye": gps_zaman[17:-5],
                "milisaniye": gps_zaman[20:-1]
            }


        }

 
       
    except:
        veri = {
                "takim_numarasi": int(2),
                "IHA_enlem": float(telemetri['lat']),
                "IHA_boylam": float(telemetri['lng']),
                "IHA_irtifa": float(telemetri['alt']),
                "IHA_dikilme": float(telemetri['pitch']),
                "IHA_yonelme": float(telemetri['yaw']),
                "IHA_yatis": float(telemetri['roll']),
                "IHA_hiz": float(telemetri['groundspeed']),
                "IHA_batarya": int(telemetri['battery_remaining']),
                "IHA_otonom": is_uav_auto,
                "IHA_kilitlenme": 0,
                "Hedef_merkez_X": 0,
                "Hedef_merkez_Y": 0,
                "Hedef_genislik": 0,
                "Hedef_yukseklik": 0,
                "GPSSaati": {
                    "saat": gps_zaman[11:-11],
                    "dakika": gps_zaman[14:-8],
                    "saniye": gps_zaman[17:-5],
                    "milisaniye": gps_zaman[20:-1]
                }

        
            }

        

    TelemetriVeriler = json.dumps(veri)

    if auth_state == True:
        if time.time()> tel_timer: 
            tel_timer=time.time()+0.5
            misson_web_socket=None
            gonderecek=json.dumps(veri)
           
            misson_web_socket = s.post(hakem_url+'/api/telemetri_gonder', json=veri)
            #misson_web_ socket= requests.post(
              #  hakem_url+'/api/telemetri_gonder', data=json.loads(gonderecek), headers={"Content-Type":"application/json"})

        if misson_web_socket.status_code == 200:
           
            if misson_web_socket['sunucusaati']=="null":
              misson_web_socket=={"sunucusaati":{'saat': veri["GPSSaati"]['saat'], 'dakika': veri["GPSSaati"]['dakika'], 'saniye': veri["GPSSaati"]['saniye'], 'milisaniye': '376'},"konumBilgileri": [{"takim_numarasi": 1,"iha_enlem": veri["IHA_enlem"],"iha_boylam": veri["IHA_boylam"],"iha_irtifa": veri["IHA_irtifa"],"iha_dikilme": veri["IHA_dikilme"],"iha_yonelme": veri["IHA_yonelme"],"iha_yatis": 0}]} 
              misson_web_socket.status_code=200
              

            print(str(misson_web_socket.status_code))
            rakip_iha_verileri = misson_web_socket.json()
        elif misson_web_socket.status_code == 401:
            print("ilk önce oturum aç oç")
        else:
            rakip_iha_verileri = "hata"
            print("Hakeme gidecek verilerde hata var!")


def on_close(ws, close_status_code, close_msg):
    print("Bağlantı sonlandırılıyor")


def on_open(ws):
    print("Bağlantı kuruldu")


websocket.enableTrace(False)
ws = websocket.WebSocketApp("ws://localhost:56781/websocket/server",
                            on_open=on_open,
                            on_message=ucaktan_veri_cekme,

                            on_close=on_close)

# =====================================================================








# yer istasyonundan alınan veriler,/takip hassasiyeti
@app.route('/oto_takip_hassasiyeti', methods=['GET', 'POST'])
def oto_takip_hassasiyeti():

    global sensitivity

    gelenveri3 = flask.request.json['sensitive']
    print(gelenveri3)
    sensitive = gelenveri3.split(",")
    print(sensitive[0], sensitive[1])
    sensitivity = [sensitive[0], sensitive[1]]
    sensitivity = list(map(float, sensitivity))
    print(sensitivity)
    return("basarili")


@app.route('/api/sunucu_saatini_al', methods=['GET'])
def sunucu_saati():

    global auth_state

    if auth_state == True:

        date_time = requests.get(
            hakem_url+'/api/sunucusaati')
        return date_time.json()

    else:

        return("İlk önce oturum açın", 400)


#Uçaktan gelen kilitlenmeye başla komutu
@app.route('/api/lock_start', methods=['POST'])
def lock_start():
    global lock_start_data
    lock_start_data = flask.request.json
    return ("Başarılı",200)
    
#Uçaktan gelen kilitlenmeye başla komutu
@app.route('/api/qrbaslat', methods=['POST'])
def qr_baslat():
    global qr_start_data
    qr_start_data = flask.request.json
    return ("Başarılı",200)   

@app.route('/api/qrbitir', methods=['POST'])
def qr_bitir():
    print("QR bitiş sinyali geldi. Kontrol Ediliyor..")
    global qr_start_data,qr_lock_counter
    qr_start_data_c=json.loads(qr_start_data)
    
    qr_end_data_c = flask.request.json
    qr_end_data_c=json.loads(qr_end_data_c)
   
    
        #ŞU ANLIK OKEY ANCAK MİLİSANİYE KONTROLÜ VE DAKİKA FARKI KONTROL EDİLECEK
    qr_lock_counter=qr_lock_counter+1
    veriqr={
            "kamikazeBaslangicZamani": 
            {
            "saat": qr_start_data_c["saat"],
            "dakika": qr_start_data_c["dakika"],
            "saniye": qr_start_data_c["saniye"],
            "milisaniye": qr_start_data_c["milisaniye"],
            },

            "kamikazeBitisZamani": 
            {
            "saat": qr_end_data_c['kamikazeBitisZamani']["saat"],
            "dakika": qr_end_data_c['kamikazeBitisZamani']["dakika"],
            "saniye": qr_end_data_c['kamikazeBitisZamani']["saniye"],
            "milisaniye": qr_end_data_c['kamikazeBitisZamani']["milisaniye"],
            },

          
             "qrMetni" : qr_end_data_c["qrMetni"]
             
            }
        
    print(veriqr)

        #Hakeme veri gönderme(API KAPALIYSA DEVRE DIŞI BIRAK)



    data_state_qr = s.post(
             hakem_url+'/api/kamikaze_bilgisi', json=veriqr
             )

   
        
       
    return ("ok")
    # date_time = requests.get(
    # hakem_url+'/api/sunucusaati')
    # return date_time.json()


   
    
#Uçaktan gelen kilitlenmeyi bitir komutu(kontrol burada yapılacak s>5)
@app.route('/api/lock_end', methods=['POST'])
def lock_end():
    print("Kilit bitiş sinyali geldi. Kontrol Ediliyor..")
    global lock_start_data,lock_counter
    lock_start_data_c=json.loads(lock_start_data)
    
    lock_end_data_c = flask.request.json
   
    
        #ŞU ANLIK OKEY ANCAK MİLİSANİYE KONTROLÜ VE DAKİKA FARKI KONTROL EDİLECEK
    lock_counter=lock_counter+1
    veri={
            "kilitlenmeBaslangicZamani": 
            {
            "saat": lock_start_data_c["saat"],
            "dakika": lock_start_data_c["dakika"],
            "saniye": lock_start_data_c["saniye"],
            "milisaniye": lock_start_data_c["milisaniye"],
            },

            "kilitlenmeBitisZamani": 
            {
            "saat": lock_end_data_c["saat"],
            "dakika": lock_end_data_c["dakika"],
            "saniye": lock_end_data_c["saniye"],
            "milisaniye": lock_end_data_c["milisaniye"],
            },

            "takim_numarasi" : int(takim_numarasi),
            "kilitlenme_numarasi" : lock_counter
            }
        
    print(veri)

        #Hakeme veri gönderme(API KAPALIYSA DEVRE DIŞI BIRAK)



    data_state = s.post(
             hakem_url+'/api/kilitlenme_bilgisi', json=veri
             )

   
        
       
    return ("ok")
    # date_time = requests.get(
    # hakem_url+'/api/sunucusaati')
    # return date_time.json()

@app.route('/api/aiset', methods=['POST'])
def ai_param_set():
   
    global aiparam
    




    gelenveri2 = flask.request.json['giden']
    

    return("basarili")
   
        
       
  
    # date_time = requests.get(
    # hakem_url+'/api/sunucusaati')
    # return date_time.json()
# yer istasyonundan alınan veriler/rakip telemetri bilgileri
@app.route('/api/yerdenucaga_telemetri', methods=['GET', 'POST'])
def yerdenucaga_telemetri():

    gelenveri2 = flask.request.json['giden']
    

    return("basarili")

# GUI'den gönderilen kadi ve sifre ile hakem apisinde oturum açma

@app.route('/api/hakem_oturum_ac', methods=['GET', 'POST'])
def hakem_oturum_ac():

    global takim_numarasi
    global auth_state

    abra_kadi = flask.request.json['kadi']
    abra_sifre = flask.request.json['sifre']
    api_giris = s.post(
        hakem_url+'/api/giris', json={'kadi': abra_kadi, 'sifre': abra_sifre})

    if not auth_state == True:
        if api_giris.status_code == 200:

            numara_veri = api_giris.json()

            takim_numarasi = numara_veri

            auth_state = True
            return (numara_veri,200)

        elif api_giris.status_code==400:
            auth_state = True
            return("hakem oturum hatası", 400)
        else:
         print(32323232)    

    else:
        return("siktir len, 2 defa oturum mu açılır amk. ya da kesin sen şimdi şifreyi yanlış yazmışsınıdr.", 400)


# yer istasyonuna gonderilern veriler/bizim telmetri
@app.route('/api/telemetrial', methods=['GET'])
def server_to_gui():
    global TelemetriVeriler

  
    return TelemetriVeriler
# GUI den ucagi yönlendirelecek koordinatalrı al ve ucak API'sine gonder


@app.route('/api/fly_to_here', methods=['POST'])
def fly_to_here():

    sonuc = requests.post(
        siha_ip+':6000/api/fly_to_here', json=flask.request.json)

    return json.dumps(sonuc)
# Rakip iha verileri


@app.route('/api/siha_telem',methods=["GET"])
def telem_get():
    global sihaTelem
    return json.dumps(sihaTelem)

@app.route('/api/komut', methods=['POST'])
def komut_post():
    global sihaKomut
    sihaKomut=flask.request.json
    return("thanks")

@app.route('/api/komut', methods=['GET'])
def komut_get():
    global sihaKomut
    return json.dumps(sihaKomut)
# yer istasyonundan alınan veriler,/takip hassasiyeti


@app.route('/api/rakip_telemetri', methods=['GET'])
def rakip_data_al():

    global rakip_iha_verileri
    print(rakip_iha_verileri)
    if rakip_iha_verileri=='':
        vktrndm= {'sunucusaati': {'gun': 16, 'saat': 11, 'dakika': 50, 'saniye': 10, 'milisaniye': 488}, 'konumBilgileri': [{'takim_numarasi': 14, 'iha_enlem': 41.5141449, 'iha_boylam': 36.1183739, 'iha_irtifa': 0.052, 'iha_dikilme': -4.0, 'iha_yonelme': -9.0, 'iha_yatis': -4.0, 'iha_hizi': 0.0, 'zaman_farki': 4}, {'takim_numarasi': 18, 'iha_enlem': 43.5765457, 'iha_boylam': 22.3854218, 'iha_irtifa': 100.0, 'iha_dikilme': 5.0, 'iha_yonelme': 256.0, 'iha_yatis': 0.0, 'iha_hizi': 223.0, 'zaman_farki': -25873019}, {'takim_numarasi': 23, 'iha_enlem': 41.512, 'iha_boylam': 36.12, 'iha_irtifa': 0.0, 'iha_dikilme': 14.0, 'iha_yonelme': 0.0, 'iha_yatis': 25.0, 'iha_hizi': 15.0, 'zaman_farki': 1848}]}

        return (vktrndm,200)
    else:  

    

     return  rakip_iha_verileri

# thread ayarları =============
th1 = threading.Thread(target=ws.run_forever)
#th2 = threading.Thread(target=app.run, args=["192.168.31.60", 4000])
th2 = threading.Thread(target=app.run, args=["192.168.31.90", 4000])
th3 = threading.Thread(target=degsoz_from_siha)

th1.start()
th2.start()
th3.start()
# ============================
