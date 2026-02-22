import os
import sys
import json
import subprocess
import urllib.request
import msvcrt

# --- НАСТРОЙКИ ---
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
MC_DIR = os.path.join(BASE_DIR, "minecraft_data")
VER_DIR = os.path.join(MC_DIR, "versions")
LIB_DIR = os.path.join(MC_DIR, "libraries")

for d in [MC_DIR, VER_DIR, LIB_DIR]: os.makedirs(d, exist_ok=True)

def draw_menu(options, idx, title="NEDOLAUNCHER"):
    os.system('cls' if os.name == 'nt' else 'clear')
    width = 55
    print("╔" + "═" * (width - 2) + "╗")
    print("║" + title.center(width - 2) + "║")
    print("╠" + "═" * (width - 2) + "╣")
    for i, opt in enumerate(options):
        char = ">" if i == idx else " "
        print(f"║ {char} {opt.ljust(width - 6)} {char} ║")
    print("╚" + "═" * (width - 2) + "╝")
    print("  " + "▀" * (width - 2))

def get_choice(options, title="МЕНЮ"):
    idx = 0
    while True:
        draw_menu(options, idx, title)
        key = ord(msvcrt.getch())
        if key == 13: return idx
        elif key == 224:
            key = ord(msvcrt.getch())
            if key == 72: idx = (idx - 1) % len(options)
            elif key == 80: idx = (idx + 1) % len(options)

def download_jar():
    """Скачивает только JAR файл версии с Mojang"""
    try:
        url = "https://launchermeta.mojang.com"
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read().decode())
            vers = [v['id'] for v in data['versions'] if v['type'] == 'release'][:15]
            
            idx = get_choice(vers + ["ОТМЕНА"], "ВЫБЕРИТЕ ВЕРСИЮ ДЛЯ ЗАГРУЗКИ JAR")
            if idx == len(vers): return
            
            ver = vers[idx]
            v_info_url = next(v['url'] for v in data['versions'] if v['id'] == ver)
            
            with urllib.request.urlopen(v_info_url) as v_res:
                v_data = json.loads(v_res.read().decode())
                jar_url = v_data['downloads']['client']['url']
                
                path = os.path.join(VER_DIR, ver)
                os.makedirs(path, exist_ok=True)
                
                print(f"\nЗагрузка {ver}.jar...")
                urllib.request.urlretrieve(jar_url, os.path.join(path, f"{ver}.jar"))
                print("Готово! Не забудьте добавить libraries вручную.")
                msvcrt.getch()
    except Exception as e:
        print(f"Ошибка: {e}")
        msvcrt.getch()

def launch_game():
    versions = [d for d in os.listdir(VER_DIR) if os.path.isdir(os.path.join(VER_DIR, d))]
    if not versions:
        print("\nВерсии не найдены в /versions/"); msvcrt.getch(); return
    
    idx = get_choice(versions + ["НАЗАД"], "ЗАПУСК ИГРЫ")
    if idx == len(versions): return
    
    ver = versions[idx]
    v_path = os.path.join(VER_DIR, ver)
    
    # Рекурсивный поиск всех .jar библиотек для ClassPath
    classpath = [os.path.join(v_path, f"{ver}.jar")]
    for root, dirs, files in os.walk(LIB_DIR):
        for file in files:
            if file.endswith(".jar"):
                classpath.append(os.path.join(root, file))

    # Склеиваем ClassPath через точку с запятой (Windows)
    cp_str = ";".join(classpath)

    # Аргументы Ely.by
    ely = [
        "-Dminecraft.api.auth.host=https://authserver.ely.by",
        "-Dminecraft.api.account.host=https://api.ely.by",
        "-Dminecraft.api.session.host=https://sessionserver.ely.by",
        "-Dminecraft.api.services.host=https://api.ely.by"
    ]

    cmd = [
        "java", "-Xmx4G", *ely,
        "-cp", cp_str,
        "net.minecraft.client.main.Main",
        "--username", "NedoPlayer",
        "--version", ver,
        "--gameDir", MC_DIR,
        "--assetsDir", os.path.join(MC_DIR, "assets"),
        "--assetIndex", "1.12", # Желательно подтянуть из JSON версии
        "--uuid", "0", "--accessToken", "0"
    ]

    print("\nПОПЫТКА ЗАПУСКА...")
    try:
        subprocess.run(cmd)
    except Exception as e:
        print(f"Ошибка запуска: {e}\nУбедитесь, что Java установлена!")
        msvcrt.getch()

def main():
    while True:
        choice = get_choice(["ИГРАТЬ", "СКАЧАТЬ КЛИЕНТ (JAR)", "ПАПКА ИГРЫ", "ВЫХОД"], "NEDOLAUNCHER CLI")
        if choice == 0: launch_game()
        elif choice == 1: download_jar()
        elif choice == 2: os.startfile(MC_DIR)
        elif choice == 3: break

if __name__ == "__main__":
    main()
