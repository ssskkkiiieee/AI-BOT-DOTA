import os
import shutil
import winreg

def get_steam_path():
    try:
        # Check current user registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return os.path.abspath(steam_path)
    except Exception:
        pass

    try:
        # Check local machine registry
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        return os.path.abspath(steam_path)
    except Exception:
        pass

    # Standard fallback paths
    fallbacks = [
        r"C:\Steam",
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        r"D:\Steam",
        r"E:\Steam"
    ]
    for path in fallbacks:
        if os.path.exists(path):
            return path
    return None

def find_dota_paths(steam_path):
    dota_paths = []
    if not steam_path:
        return dota_paths

    # Primary library folder
    primary_dota = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
    if os.path.exists(primary_dota):
        dota_paths.append(primary_dota)

    # Search other Steam library folders from libraryfolders.vdf
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Simple parsing of vdf file
            import re
            paths = re.findall(r'"path"\s+"([^"]+)"', content)
            for path in paths:
                # Replace double backslashes
                path = path.replace("\\\\", "\\")
                dota_path = os.path.join(path, "steamapps", "common", "dota 2 beta")
                if os.path.exists(dota_path) and dota_path not in dota_paths:
                    dota_paths.append(dota_path)
        except Exception as e:
            print(f"[Предупреждение] Не удалось прочитать libraryfolders.vdf: {e}")

    return dota_paths

def main():
    print("=== Установка Dota 2 AI Бота (Локальное лобби) ===")
    
    source_lua = r"C:\бот\bot_generic.lua"
    if not os.path.exists(source_lua):
        print(f"[Ошибка] Файл бота не найден по пути: {source_lua}")
        return

    steam_path = get_steam_path()
    if steam_path:
        print(f"[Инфо] Найден путь Steam: {steam_path}")
    else:
        print("[Предупреждение] Не удалось автоматически найти Steam.")

    dota_paths = find_dota_paths(steam_path)
    
    # If not found automatically, let's ask for manual verification or use a default fallback
    if not dota_paths:
        print("[Внимание] Не удалось найти установленную Dota 2 автоматически.")
        print("Пожалуйста, введите путь к вашей папке 'dota 2 beta' вручную.")
        print("Например: C:\\Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta")
        manual_path = input("Путь к dota 2 beta (или нажмите Enter для пропуска): ").strip()
        if manual_path and os.path.exists(manual_path):
            dota_paths = [manual_path]

    if not dota_paths:
        print("\n[Ошибка] Не найдено папок Dota 2. Копирование невозможно.")
        print("Пожалуйста, скопируйте файл C:\\бот\\bot_generic.lua вручную в:")
        print("<Ваш Steam>\\steamapps\\common\\dota 2 beta\\game\\dota\\scripts\\vscripts\\bots\\bot_generic.lua")
        return

    for dota_path in dota_paths:
        print(f"\n[Инфо] Найдена папка Dota 2: {dota_path}")
        
        # Target directory: game/dota/scripts/vscripts/bots
        target_dir = os.path.join(dota_path, "game", "dota", "scripts", "vscripts", "bots")
        os.makedirs(target_dir, exist_ok=True)
        
        target_file = os.path.join(target_dir, "bot_generic.lua")
        try:
            shutil.copy2(source_lua, target_file)
            print(f"[Успех] Файл скопирован в: {target_file}")
        except Exception as e:
            print(f"[Ошибка] Не удалось скопировать файл в {target_file}: {e}")

    print("\n" + "="*50)
    print("=== ИНСТРУКЦИЯ ПО ЗАПУСКУ ИГРЫ ===")
    print("="*50)
    print("1. Запустите prediction сервер ИИ:")
    print("   Откройте новый терминал и выполните:")
    print("   python C:\\бот\\server.py")
    print("\n2. Запустите Dota 2.")
    print("3. Создайте Локальное лобби (Играть -> Создать лобби -> Локальный сервер).")
    print("4. Зайдите в Настройки лобби:")
    print("   - Включите галочку 'Заполнить ботами'.")
    print("   - В выпадающем списке выбора ботов выберите 'Локальные боты' (Local Bots).")
    print("5. Начните игру.")
    print("6. Ваш ИИ-бот будет перехватывать действия героев в реальном времени, опрашивая сервер на порту 8080!")
    print("="*50)

if __name__ == "__main__":
    main()
