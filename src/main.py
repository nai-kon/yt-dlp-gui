import os
import platform
import re
import threading
import tkinter
import tkinter.filedialog
import tkinter.messagebox

import customtkinter as ctk
from PIL import ImageTk
from yt_dlp import YoutubeDL

from config_manager import ConfigManager


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Video Downloader")
        self.geometry("550x300")

        # ディレクトリ選択（ラベル＋選択ボタンを横並びで表示）
        self.config = ConfigManager()
        self.selected_dir = self.config.data.get("download_dir", None)

        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.pack(padx=20, pady=10, fill="x")

        self.dir_label = ctk.CTkLabel(
            self.dir_frame,
            text=f"保存先: {self.selected_dir if self.selected_dir else '未選択'}",
            anchor="w"
        )
        self.dir_label.pack(side="left", fill="x", expand=True)

        self.dir_button = ctk.CTkButton(self.dir_frame, text="選択", width=50, command=self.select_directory)
        self.dir_button.pack(side="right", padx=(5, 0))

        # URL入力 + ダウンロードボタンを右端に配置
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.pack(padx=20, pady=(10, 5), fill="x")

        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="URLを入力 or Ctrl+Vで貼り付け")
        self.url_entry.pack(side="left", fill="x", expand=True)

        self.download_button = ctk.CTkButton(self.url_frame, text="開始", width=50, command=self.start_download)
        self.download_button.pack(side="right", padx=(5, 0))

        # ステータステキストボックス
        self.status_text = ctk.CTkTextbox(self, height=40)
        self.status_text.pack(padx=20, pady=5, fill="both", expand=True)
        self.status_text.configure(state="disabled")

        # プログレスバー
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(padx=20, pady=(5, 10), fill="x")

        # アプリ上でCtrl+Vを押したときにURLを貼り付けてダウンロード開始
        def global_paste(event=None):
            text = self.clipboard_get()
            if self.is_valid_url(text):
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, text)
                self.start_download()

        self.bind_all("<Control-v>", global_paste)
        self.bind_all("<Command-v>", global_paste)  # for mac

        # ウィンドウがアクティブになったときにクリップボードにURLがあればDL開始
        # def handle_window_activate(event=None):
        #     global_paste()

        # self.bind_all("<FocusIn>", handle_window_activate)


        # 起動時にURLがあればDL開始
        # global_paste()

    def rename_file(self, url: str, video_info: dict) -> None | str:
        def rotate_filename(username: str) -> str:
            if os.path.exists(f"{self.selected_dir}/{username}.mp4"):
                # ファイル名が重複したら連番を付与
                for i in range(1, 100):
                    username = f"{username}_{i}"
                    if not os.path.exists(f"{self.selected_dir}/{username}.mp4"):
                        break
                else:
                    raise Exception("同じユーザー名のファイルが多すぎます。")
            return username
        
        
        if url.startswith("https://x.com/") and (uploader_id:= video_info.get("uploader_id", None)) is not None:
            return rotate_filename(uploader_id)

        if url.startswith("https://www.facebook.com/") and (uploader:= video_info.get("uploader", None)) is not None:
            return rotate_filename(uploader)

        if url.startswith("https://www.tiktok.com/"):
            # URLからユーザー名を抽出
            if (username:= re.match(r"https://www\.tiktok\.com/@([^/]+)/", url)) is not None:
                return rotate_filename(username.group(1))

        return None

    def start_download(self) -> None:
        self.progress.set(0)
        url = self.url_entry.get().strip()
        if not self.is_valid_url(url):
            tkinter.messagebox.showerror("エラー", f"不正なURLです。\n{url}")
            return
        if not self.selected_dir:
            tkinter.messagebox.showerror("エラー", "保存先ディレクトリを選択してください。")
            return

        def run_download(url: str) -> None:
            def progress_hook(d):
                if d["status"] == "downloading":
                    # self.progress.set( / 100)  # the value jitters so dont use
                    self.progress.set(d.get("downloaded_bytes", 0) / d.get("total_bytes", 1))

            self.download_button.configure(state="disabled")
            self.set_status("情報取得中...")

            try:
                options = {
                    "outtmpl": f"{self.selected_dir}/%(title)s.%(ext)s",
                    "progress_hooks": [progress_hook],
                    "cookiesfrombrowser": ("firefox",),
                }

                if url.startswith("https://www.youtube.com/"):
                    options.pop("cookiesfrombrowser", None)  # 指定すると何故か4k動画がDLできないので当面外す

                # 最初にメタ情報を取得して表示
                with YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=False)
                    self.set_status(info["title"][:35] + "...")

                # xとtiktokはユーザー名をファイル名にする
                if (user_name := self.rename_file(url, info)) is not None:
                    options["outtmpl"] = f"{self.selected_dir}/{user_name}.%(ext)s"

                # ダウンロード実行
                with YoutubeDL(options) as ydl:
                    ydl.download(url)
                    self.append_status("ダウンロード完了")
                    self.progress.set(1.0)

            except Exception as e:
                self.append_status("エラー発生")
                tkinter.messagebox.showerror("エラー", f"ダウンロード中にエラーが発生しました。\n{e}")
            
            finally:
                self.download_button.configure(state="normal")

        threading.Thread(target=run_download, args=(url,), daemon=True).start()

    def is_valid_url(self, url: str) -> bool:
        """対応URLかチェック"""
        valid_prefixes = [
            "https://www.youtube.com/watch?v=",
            "https://www.youtube.com/shorts/",
            "https://x.com/",
            "https://www.tiktok.com/",
            "https://www.facebook.com/",
            "https://www.instagram.com/"
        ]
        return any(url.startswith(prefix) for prefix in valid_prefixes)

    def select_directory(self) -> None:
        dir_path = tkinter.filedialog.askdirectory(initialdir=self.selected_dir)
        if dir_path:
            self.selected_dir = dir_path
            self.dir_label.configure(text=f"保存先: {dir_path}")
            self.config.data["download_dir"] = dir_path
            self.config.save()

    def append_status(self, message: str) -> None:
        self.status_text.configure(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    def set_status(self, message: str) -> None:
        self.status_text.configure(state="normal")
        self.status_text.delete("0.0", "end")
        self.status_text.insert("end", message + "\n")
        self.status_text.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    if platform.system() == "Windows":
        app.wm_iconbitmap()
        app.iconphoto(False, ImageTk.PhotoImage(file="logo.ico"))
    app.mainloop()
