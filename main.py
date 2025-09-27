import json
import threading
import tkinter.filedialog
import tkinter.messagebox

import customtkinter as ctk
from yt_dlp import YoutubeDL

from config_manager import ConfigManager


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Video Downloader")
        self.geometry("500x300")

        # URL入力
        self.url_entry = ctk.CTkEntry(self, placeholder_text="URLを入力 or Ctrl+Vで貼り付け")
        self.url_entry.pack(padx=20, pady=5, fill="x")

        # ディレクトリ選択（ボタンテキストに保存先を表示）
        self.config = ConfigManager()
        self.selected_dir = self.config.data.get("download_dir", None)
        self.dir_button = ctk.CTkButton(self, text=f"保存先: {self.selected_dir if self.selected_dir else '未選択'}", command=self.select_directory, anchor="w")
        self.dir_button.pack(padx=20, pady=10, fill="x")

        # アプリ上でCtrl+Vを押したときにURLを貼り付けてダウンロード開始
        def global_paste(event=None):
            text = self.clipboard_get()
            if self.is_valid_url(text):
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, text)
                self.start_download()

        self.bind_all("<Control-v>", global_paste)

        # ダウンロードボタン
        self.download_button = ctk.CTkButton(self, text="ダウンロード", command=self.start_download)
        self.download_button.pack(padx=20, pady=5, fill="x")

        # プログレスバー
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(padx=20, pady=5, fill="x")

        # ステータステキストボックス
        self.status_text = ctk.CTkTextbox(self, height=60)
        self.status_text.pack(padx=20, pady=5, fill="both", expand=True)
        self.status_text.configure(state="disabled")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not self.is_valid_url(url):
            self.append_status(f"不正なURLです: {url}")
            tkinter.messagebox.showerror("エラー", f"不正なURLです。\n{url}")
            return
        if not self.selected_dir:
            self.append_status("保存先ディレクトリを選択してください。")
            tkinter.messagebox.showerror("エラー", "保存先ディレクトリを選択してください。")
            return

        def run_download(url: str):
            def progress_hook(d):
                if d["status"] == "downloading":
                    self.progress.set(d.get("_percent", "0") / 100)
            
            self.reset_status()
            self.append_status(f"ダウンロードを開始: {url}")

            options = {
                "outtmpl": f"{self.selected_dir}/%(title)s.%(ext)s",
                "progress_hooks": [progress_hook],
            }

            with YoutubeDL(options) as ydl:
                # 最初にメタ情報を取得して表示
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)
                self.append_status(info["title"][:35] + "...")

                self.progress.set(0.01)  # 最初に少し進捗を表示
                ydl.download(url)

            self.append_status("ダウンロード完了")

        threading.Thread(target=run_download, args=(url,), daemon=True).start()

    def is_valid_url(self, url: str) -> bool:
        """対応するURLが有効かどうかをチェック"""
        valid_prefixes = [
            "https://www.youtube.com/watch?v=",
            "https://www.youtube.com/shorts/",
            # 今後追加可能
        ]
        return any(url.startswith(prefix) for prefix in valid_prefixes)

    def select_directory(self):
        dir_path = tkinter.filedialog.askdirectory()
        if dir_path:
            self.selected_dir = dir_path
            self.dir_button.configure(text=f"保存先: {dir_path}")
            self.config.data["download_dir"] = dir_path
            self.config.save()

    def append_status(self, message):
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    def reset_status(self):
        self.status_text.configure(state="normal")
        self.status_text.delete("0.0", "end")
        self.status_text.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()
