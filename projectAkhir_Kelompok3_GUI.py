import tkinter as tk
import os
from tkinter import messagebox
from tkinter import simpledialog
from abc import ABC, abstractmethod
from enum import Enum
from PIL import Image, ImageTk

# === Model & Logic ===
class Role(Enum):
    ADMIN = "admin"
    PEMILIH = "pemilih"

class User(ABC):
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def check_password(self, password):
        return self._password == password

    @abstractmethod
    def menu(self, app):
        pass

    @property
    def username(self):
        return self._username

class Admin(User):
    def menu(self, app):
        app.show_admin_menu(self)

class Pemilih(User):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.__sudah_memilih = False

    def menu(self, app):
        app.show_voter_menu(self, self.__sudah_memilih)

    def set_sudah_memilih(self, val):
        self.__sudah_memilih = val

    def sudah_memilih(self):
        return self.__sudah_memilih

class Kandidat(ABC):
    def __init__(self, nama):
        self._nama = nama

    @property
    def nama(self):
        return self._nama

    @abstractmethod
    def tampilkan_info(self):
        pass

class Ketua(Kandidat):
    def tampilkan_info(self):
        return f"Ketua: {self._nama}"

class Wakil(Kandidat):
    def tampilkan_info(self):
        return f"Wakil: {self._nama}"

class PasanganKandidat:
    def __init__(self, ketua: Ketua, wakil: Wakil, visi: str, gambar_path=None):
        self._ketua = ketua
        self._wakil = wakil
        self._visi = visi
        self._gambar_path = gambar_path  # path gambar pasangan

    @property
    def nama_pasangan(self):
        return f"{self._ketua.nama} & {self._wakil.nama}"

    @property
    def gambar_path(self):
        return self._gambar_path

    def tampilkan_info(self):
        return f"{self._ketua.nama} (Ketua) & {self._wakil.nama} (Wakil)\nVisi: {self._visi}"

class VotingSystem:
    def __init__(self):
        self._pasangan_kandidat = []
        self._suara = {}
        self._log_voting = {}

    def tambah_pasangan(self, pasangan: PasanganKandidat):
        self._pasangan_kandidat.append(pasangan)
        self._suara[pasangan.nama_pasangan] = 0

    def get_kandidat_list(self):
        return self._pasangan_kandidat

    def get_pasangan_by_index(self, index):
        if 0 <= index < len(self._pasangan_kandidat):
            return self._pasangan_kandidat[index]
        return None

    def tambah_suara(self, pasangan: PasanganKandidat):
        self._suara[pasangan.nama_pasangan] += 1

    def log_voting(self, username, pasangan_nama):
        self._log_voting[username] = pasangan_nama

    def get_log_voting(self):
        return self._log_voting

    def get_hasil(self):
        total_suara = sum(self._suara.values())
        hasil = []
        if total_suara == 0:
            return hasil, None
        pemenang = max(self._suara, key=self._suara.get)
        for nama, jumlah in self._suara.items():  # <-- diperbaiki unpacking
            persentase = (jumlah / total_suara) * 100
            hasil.append((nama, jumlah, persentase))
        return hasil, pemenang

class LoginManager:
    def __init__(self, users, admin_password):
        self._users = {user.username: user for user in users}
        self._admin_password = admin_password

    def login(self, username, password):
        user = self._users.get(username)
        if user and user.check_password(password):
            return user
        else:
            return None

    def register_pemilih(self, username, password):
        if username in self._users:
            return False
        new_user = Pemilih(username, password)
        self._users[username] = new_user
        return True

    def get_user(self, username):
        return self._users.get(username)

# === GUI Section ===
class VotingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistem Voting - GUI")
        self.geometry("800x600")
        self.resizable(False, False)

        # --- Background Gradient ---
        self.bg_canvas = tk.Canvas(self, width=800, height=600, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.draw_gradient("#e0eafc", "#cfdef3")

        # --- Main Frame ---
        self.main_frame = tk.Frame(self.bg_canvas, bg="#ffffff")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", width=700, height=520)

        # Data
        self.users = [
            Admin("admin", "admin123"),
            Pemilih("dina", "111"),
            Pemilih("eko", "222"),
            Pemilih("sari", "333")
        ]
        self.login_manager = LoginManager(self.users, admin_password="admin123")
        self.voting_system = VotingSystem()
        # Tambahkan path gambar sesuai file gambar Anda
        self.voting_system.tambah_pasangan(PasanganKandidat(Ketua("Andi"), Wakil("Dewi"), "Transparan dan adil", "andi_dewi.png"))
        self.voting_system.tambah_pasangan(PasanganKandidat(Ketua("Budi"), Wakil("Eka"), "Amanah dan tegas", "budi_eka.png"))
        self.voting_system.tambah_pasangan(PasanganKandidat(Ketua("Candra"), Wakil("Fajar"), "Bersatu dan maju", "candra_fajar.png"))

        self.current_user = None
        self.logo_img = None
        self.kandidat_imgs = []  # Untuk menyimpan referensi gambar kandidat
        self.show_main_menu()

    def draw_gradient(self, color1, color2):
        # Simple vertical gradient
        for i in range(0, 600):  # <-- diperbaiki agar sesuai tinggi window
            r1, g1, b1 = self.winfo_rgb(color1)
            r2, g2, b2 = self.winfo_rgb(color2)
            r = int(r1 + (r2 - r1) * i / 600) >> 8
            g = int(g1 + (g2 - g1) * i / 600) >> 8
            b = int(b1 + (b2 - b1) * i / 600) >> 8
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.bg_canvas.create_line(0, i, 800, i, fill=color)

    # --- Animasi Marquee (lebih smooth) ---
    def marquee(self, label, text, delay=60):
        def scroll():
            marquee_text = label.cget("text")
            marquee_text = marquee_text[1:] + marquee_text[0]
            label.config(text=marquee_text)
            label.after(delay, scroll)
        label.config(text=text)
        scroll()

    # --- Utility: Entry dengan Placeholder ---
    def entry_with_placeholder(self, parent, placeholder, show=None):
        entry = tk.Entry(parent, font=("Segoe UI", 11), show=show if show else "")
        entry.insert(0, placeholder)
        entry.config(fg="#b2bec3")
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="#2d3436", show=show if show else "")
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="#b2bec3", show="")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        return entry

    # --- Utility: Button Style Modern ---
    def styled_button(self, parent, text, command, icon=None):
        btn = tk.Button(parent, text=f"{icon+' ' if icon else ''}{text}", width=28, font=("Segoe UI", 13, "bold"),
                        bg="#2980b9", fg="white", activebackground="#3498db", activeforeground="white",
                        bd=0, relief="flat", cursor="hand2", command=command)
        btn.bind("<Enter>", lambda e: btn.config(bg="#3498db"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#2980b9"))
        return btn

    # --- Main Menu ---
    def show_main_menu(self):
        self.clear_frame()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path).resize((120, 120))
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(self.main_frame, image=self.logo_img, bg="#ffffff").pack(pady=(28, 10))
        else:
            tk.Label(self.main_frame, text="🗳️", font=("Segoe UI", 70), bg="#ffffff").pack(pady=(28, 10))

        title = tk.Label(self.main_frame, text="SISTEM VOTING", font=("Poppins", 24, "bold"),
                         bg="#ffffff", fg="#2e86c1")
        title.pack(pady=(0, 10))

        # Animasi teks berjalan
        marquee_label = tk.Label(self.main_frame, font=("Segoe UI", 12), bg="#ffffff", fg="#117864")
        marquee_label.pack()
        self.marquee(marquee_label, "   Selamat datang di Sistem Voting Kelompok 3! Pilih pemimpin favoritmu dengan semangat! 🎉   ")

        # Tambahkan quote random
        import random
        quotes = [
            "🌟 Satu suara Anda sangat berarti!",
            "💡 Jadilah bagian dari perubahan!",
            "🔥 Voting hari ini, untuk masa depan esok!",
            "😃 Jangan lupa tersenyum saat memilih!"
        ]
        tk.Label(self.main_frame, text=random.choice(quotes), font=("Segoe UI", 11, "italic"), bg="#ffffff", fg="#636e72").pack(pady=(0, 8))

        self.styled_button(self.main_frame, "Login", self.show_login, icon="🔑").pack(pady=12)
        self.styled_button(self.main_frame, "Registrasi Pemilih", self.show_register, icon="📝").pack(pady=12)
        self.styled_button(self.main_frame, "Keluar", self.quit, icon="❌").pack(pady=12)

    # --- Login Window ---
    def show_login(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Login", font=("Poppins", 18, "bold"), bg="#ffffff").pack(pady=18)
        entry_user = self.entry_with_placeholder(self.main_frame, "Username")
        entry_user.pack(pady=4)
        entry_pass = self.entry_with_placeholder(self.main_frame, "Password", show="*")
        entry_pass.pack(pady=4)

        def do_login():
            username = entry_user.get()
            password = entry_pass.get()
            if username == "Username": username = ""
            if password == "Password": password = ""
            user = self.login_manager.login(username, password)
            if user:
                self.current_user = user
                messagebox.showinfo("Sukses", f"Login berhasil sebagai {user.username}")
                user.menu(self)
            else:
                messagebox.showerror("Gagal", "Username atau password salah.")

        self.styled_button(self.main_frame, "Login", do_login, icon="🔑").pack(pady=10)
        self.styled_button(self.main_frame, "Kembali", self.show_main_menu, icon="⬅️").pack()

    # --- Register Window ---
    def show_register(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Registrasi Pemilih", font=("Poppins", 18, "bold"), bg="#ffffff").pack(pady=18)
        entry_user = self.entry_with_placeholder(self.main_frame, "Username")
        entry_user.pack(pady=4)
        entry_pass = self.entry_with_placeholder(self.main_frame, "Password", show="*")
        entry_pass.pack(pady=4)

        def do_register():
            username = entry_user.get()
            password = entry_pass.get()
            if username == "Username": username = ""
            if password == "Password": password = ""
            if not username or not password:
                messagebox.showwarning("Peringatan", "Username dan password harus diisi.")
                return
            if self.login_manager.register_pemilih(username, password):
                messagebox.showinfo("Sukses", "Registrasi berhasil. Silakan login.")
                self.show_login()
            else:
                messagebox.showerror("Gagal", "Username sudah digunakan.")

        self.styled_button(self.main_frame, "Daftar", do_register, icon="📝").pack(pady=10)
        self.styled_button(self.main_frame, "Kembali", self.show_main_menu, icon="⬅️").pack()

    # --- Admin Menu ---
    def show_admin_menu(self, user):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Menu Admin ({user.username})", font=("Poppins", 16, "bold"), bg="#ffffff").pack(pady=18)
        self.styled_button(self.main_frame, "Lihat Kandidat", self.show_kandidat, icon="👥").pack(pady=7)
        self.styled_button(self.main_frame, "Lihat Hasil Voting", self.show_hasil, icon="📊").pack(pady=7)
        self.styled_button(self.main_frame, "Lihat Log Voting", self.show_log, icon="📝").pack(pady=7)
        self.styled_button(self.main_frame, "Logout", self.logout, icon="⬅️").pack(pady=14)

    # --- Pemilih Menu ---
    def show_voter_menu(self, user, sudah_memilih):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Menu Pemilih ({user.username})", font=("Poppins", 16, "bold"), bg="#ffffff").pack(pady=18)
        btn_vote = self.styled_button(self.main_frame, "Voting", lambda: self.show_voting(user), icon="🗳️")
        btn_vote.pack(pady=7)
        if sudah_memilih:
            btn_vote.config(state="disabled")
            tk.Label(self.main_frame, text="Anda sudah melakukan voting.", fg="red", bg="#ffffff", font=("Segoe UI", 10, "italic")).pack()
        self.styled_button(self.main_frame, "Logout", self.logout, icon="⬅️").pack(pady=14)

    # --- Kandidat List (Card Style) ---
    def show_kandidat(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Daftar Pasangan Kandidat", font=("Poppins", 14, "bold"), bg="#ffffff").pack(pady=18)
        self.kandidat_imgs = []

        for i, pasangan in enumerate(self.voting_system.get_kandidat_list()):
            card = self.create_card(self.main_frame, "#f4f8fb")
            card.pack(anchor="w", padx=30, pady=8, fill="x")
            if pasangan.gambar_path and os.path.exists(pasangan.gambar_path):
                img = Image.open(pasangan.gambar_path).resize((70, 70))
                img_tk = ImageTk.PhotoImage(img)
                self.kandidat_imgs.append(img_tk)
                tk.Label(card, image=img_tk, bg="#f4f8fb").pack(side="left", padx=10)
            else:
                tk.Label(card, text="🧑‍🤝‍🧑", font=("Segoe UI", 38), bg="#f4f8fb").pack(side="left", padx=10)
            info = pasangan.tampilkan_info()
            tk.Label(card, text=f"{i+1}. {info}", bg="#f4f8fb", justify="left", anchor="w", font=("Segoe UI", 12)).pack(side="left", padx=8)

        self.styled_button(self.main_frame, "Kembali", lambda: self.current_user.menu(self), icon="⬅️").pack(pady=14)

    # --- Voting Window (Card Style) ---
    def show_voting(self, user):
        self.clear_frame()
        tk.Label(self.main_frame, text="Voting", font=("Poppins", 14, "bold"), bg="#ffffff").pack(pady=18)
        kandidat_list = self.voting_system.get_kandidat_list()
        var = tk.IntVar(value=-1)
        self.kandidat_imgs = []

        for i, pasangan in enumerate(kandidat_list):
            card = self.create_card(self.main_frame, "#f4f8fb")
            card.pack(anchor="w", padx=30, pady=8, fill="x")
            if pasangan.gambar_path and os.path.exists(pasangan.gambar_path):
                img = Image.open(pasangan.gambar_path).resize((70, 70))
                img_tk = ImageTk.PhotoImage(img)
                self.kandidat_imgs.append(img_tk)
                tk.Label(card, image=img_tk, bg="#f4f8fb").pack(side="left", padx=10)
            else:
                tk.Label(card, text="🧑‍🤝‍🧑", font=("Segoe UI", 38), bg="#f4f8fb").pack(side="left", padx=10)
            info = pasangan.tampilkan_info()
            tk.Radiobutton(card, text=info, variable=var, value=i, bg="#f4f8fb", anchor="w", justify="left", font=("Segoe UI", 13)).pack(side="left", padx=8)

        def submit_vote():
            idx = var.get()
            if idx == -1:
                messagebox.showwarning("Peringatan", "Pilih salah satu pasangan kandidat. Semangat memilih! 💪")
                return
            pasangan = self.voting_system.get_pasangan_by_index(idx)
            self.voting_system.tambah_suara(pasangan)
            self.voting_system.log_voting(user.username, pasangan.nama_pasangan)
            user.set_sudah_memilih(True)
            messagebox.showinfo("Sukses", f"Terima kasih sudah memilih pasangan: {pasangan.nama_pasangan}! 🎊")
            self.show_voter_menu(user, True)

        self.styled_button(self.main_frame, "Vote", submit_vote, icon="✅").pack(pady=10)
        self.styled_button(self.main_frame, "Kembali", lambda: self.show_voter_menu(user, user.sudah_memilih()), icon="⬅️").pack()

    # --- Hasil Voting (Card Style) ---
    def show_hasil(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Hasil Voting", font=("Poppins", 14, "bold"), bg="#ffffff").pack(pady=18)
        hasil, pemenang = self.voting_system.get_hasil()
        kandidat_list = self.voting_system.get_kandidat_list()
        self.kandidat_imgs = []

        if not hasil:
            tk.Label(self.main_frame, text="Belum ada suara masuk.", bg="#ffffff").pack()
        else:
            for nama, jumlah, persen in hasil:
                pasangan = next((k for k in kandidat_list if k.nama_pasangan == nama), None)
                card = tk.Frame(self.main_frame, bg="#f4f8fb", bd=1, relief="solid", highlightbackground="#dfe6e9", highlightthickness=1)
                card.pack(anchor="w", padx=30, pady=4, fill="x")
                if pasangan and pasangan.gambar_path and os.path.exists(pasangan.gambar_path):
                    img = Image.open(pasangan.gambar_path).resize((60, 60))
                    img_tk = ImageTk.PhotoImage(img)
                    self.kandidat_imgs.append(img_tk)
                    tk.Label(card, image=img_tk, bg="#f4f8fb").pack(side="left", padx=6)
                else:
                    tk.Label(card, text="🧑‍🤝‍🧑", font=("Segoe UI", 28), bg="#f4f8fb").pack(side="left", padx=6)
                tk.Label(card, text=f"{nama}: {jumlah} suara ({persen:.2f}%)", bg="#f4f8fb", font=("Segoe UI", 12)).pack(side="left", padx=8)

            winner_frame = tk.Frame(self.main_frame, bg="#ffffff")
            winner_frame.pack(pady=(18, 0))
            winner_label = tk.Label(
                winner_frame,
                text=f"🏆 Pemenang: {pemenang}",
                font=("Segoe UI", 13, "bold"),
                fg="#d35400",
                bg="#ffffff"
            )
            winner_label.pack()

            def blink(count=0):
                if count < 8:
                    fg = "#d35400" if count % 2 == 0 else "#ffffff"
                    if winner_label.winfo_exists():
                        winner_label.config(fg=fg)
                        self.after(500, lambda: blink(count + 1))
                else:
                    if winner_label.winfo_exists():
                        winner_label.config(fg="#d35400")
            blink()

        self.styled_button(self.main_frame, "Kembali", lambda: self.current_user.menu(self), icon="⬅️").pack(pady=14)

    # --- Log Voting (Card Style) ---
    def show_log(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Log Voting", font=("Poppins", 14, "bold"), bg="#ffffff").pack(pady=18)
        log = self.voting_system.get_log_voting()
        if not log:
            tk.Label(self.main_frame, text="😅 Belum ada data voting. Yuk, ramaikan dengan suara kamu!", bg="#ffffff", fg="#e17055", font=("Segoe UI", 12, "italic")).pack()
        else:
            for username, pilihan in log.items():
                card = tk.Frame(self.main_frame, bg="#f4f8fb", bd=1, relief="solid", highlightbackground="#dfe6e9", highlightthickness=1)
                card.pack(anchor="w", padx=30, pady=4, fill="x")
                tk.Label(card, text=f"👤 {username} memilih {pilihan} 🎉", bg="#f4f8fb", font=("Segoe UI", 12, "bold"), fg="#0984e3").pack(anchor="w", padx=8)
        self.styled_button(self.main_frame, "Kembali", lambda: self.current_user.menu(self), icon="⬅️").pack(pady=14)

    # --- Logout ---
    def logout(self):
        self.current_user = None
        self.show_main_menu()

    # --- Utility ---
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def create_card(self, parent, bg, **kwargs):
        # Card dengan efek shadow dan hover
        shadow = tk.Frame(parent, bg="#dfe6e9")
        shadow.pack(anchor="w", padx=32, pady=10, fill="x")
        card = tk.Frame(shadow, bg=bg, bd=0, relief="flat", highlightthickness=0, **kwargs)
        card.pack(padx=2, pady=2, fill="x")

        def on_enter(e):
            card.config(bg="#eaf6fb")
        def on_leave(e):
            card.config(bg=bg)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        return card

if __name__ == "__main__":
    app = VotingApp()
    app.mainloop()