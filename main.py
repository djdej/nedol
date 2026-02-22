import os
import subprocess
import threading
import customtkinter as ctk
import minecraft_launcher_lib

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") # Более "майнкрафтовский" стиль

class FastLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MC Local Launcher")
        self.geometry("850x550")
        
        self.minecraft_dir = os.path.join(os.getcwd(), "minecraft_data")
        self.versions_dir = os.path.join(self.minecraft_dir, "versions")
        os.makedirs(self.versions_dir, exist_ok=True)

        self.setup_ui()
        self.refresh_lists()

    def setup_ui(self):
        # Боковая панель
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="LAUNCHER", font=("Impact", 28)).pack(pady=20)
        
        self.user_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Никнейм")
        self.user_entry.insert(0, "Player")
        self.user_entry.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.sidebar, text="RAM (GB):").pack(padx=20, anchor="w")
        self.ram_slider = ctk.CTkSlider(self.sidebar, from_=1, to=16, number_of_steps=15)
        self.ram_slider.set(4)
        self.ram_slider.pack(pady=10, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Готов", text_color="gray")
        self.status_label.pack(side="bottom", pady=20)

        # Основная область
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.tabs = ctk.CTkTabview(self.main)
        self.tabs.pack(fill="both", expand=True)
        self.tab_local = self.tabs.add("Мои версии (Локальные)")
        self.tab_remote = self.tabs.add("Доступные релизы")

        self.scroll_local = ctk.CTkScrollableFrame(self.tab_local)
        self.scroll_local.pack(fill="both", expand=True)
        
        self.scroll_remote = ctk.CTkScrollableFrame(self.tab_remote)
        self.scroll_remote.pack(fill="both", expand=True)

        self.selected_v = ctk.StringVar()

        # Кнопка запуска
        self.btn_play = ctk.CTkButton(self.main, text="ЗАПУСТИТЬ ИГРУ", height=60, 
                                      font=("Roboto", 20, "bold"), command=self.handle_launch)
        self.btn_play.pack(fill="x", pady=(20, 0))

    def refresh_lists(self):
        # 1. Локальные версии (просто папки в /versions)
        for w in self.scroll_local.winfo_children(): w.destroy()
        locals = [f for f in os.listdir(self.versions_dir) if os.path.isdir(os.path.join(self.versions_dir, f))]
        for v in locals:
            ctk.CTkRadioButton(self.scroll_local, text=v, variable=self.selected_v, value=v).pack(anchor="w", pady=5)

        # 2. Список из сети (только ID)
        def load_remote():
            try:
                remotes = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == 'release']
                for v in remotes[:40]:
                    ctk.CTkRadioButton(self.scroll_remote, text=f"Release {v}", variable=self.selected_v, value=v).pack(anchor="w", pady=2)
            except: pass
        threading.Thread(target=load_remote, daemon=True).start()

    def handle_launch(self):
        version = self.selected_v.get()
        if not version: return

        # Проверяем, существует ли папка версии локально
        version_path = os.path.join(self.versions_dir, version)
        
        if os.path.exists(version_path):
            # МГНОВЕННЫЙ ЗАПУСК
            threading.Thread(target=self.run_minecraft, args=(version, False), daemon=True).start()
        else:
            # СНАЧАЛА СКАЧИВАЕМ
            threading.Thread(target=self.run_minecraft, args=(version, True), daemon=True).start()

    def run_minecraft(self, version, need_download):
        self.btn_play.configure(state="disabled", text="ЗАГРУЗКА..." if need_download else "ЗАПУСК...")
        
        try:
            if need_download:
                self.status_label.configure(text="Скачивание файлов...")
                minecraft_launcher_lib.install.install_minecraft_version(version, self.minecraft_dir)
                self.refresh_lists() # Обновить список локальных после скачивания

            options = {
                "username": self.user_entry.get(),
                "jvmArguments": [f"-Xmx{int(self.ram_slider.get())}G"]
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(version, self.minecraft_dir, options)
            
            self.status_label.configure(text="Игра в процессе", text_color="#2da44e")
            self.withdraw()
            subprocess.run(command)
            self.deiconify()
            self.status_label.configure(text="Готов", text_color="gray")

        except Exception as e:
            self.status_label.configure(text="Ошибка!", text_color="red")
            print(f"Ошибка запуска: {e}")
            self.deiconify()
        
        self.btn_play.configure(state="normal", text="ЗАПУСТИТЬ ИГРУ")

if __name__ == "__main__":
    app = FastLauncher()
    app.mainloop()
