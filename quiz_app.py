"""Quiz Interaktif - Tugas Akhir (Tkinter).

Fitur:
- 10 soal pilihan ganda dengan Radiobutton (urutan soal dan opsi diacak)
- Timer 30 detik per soal dengan bar yang berubah warna
- Skor real-time dan progress bar soal
- Validasi: jawaban harus dipilih sebelum dikirim
- Animasi: kilau hijau/merah, getar saat salah atau belum memilih, skor berdenyut
- Keyboard: Enter kirim/lanjut, Esc lewati, 1-4 pilih jawaban
- State tersimpan di quiz_progress.json, jadi quiz bisa dilanjutkan
"""
import json
import math
import os
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk

WAKTU_PER_SOAL = 30
POIN_BENAR = 10
FILE_PROGRESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_progress.json")

FONT = "Helvetica"
WARNA = {
    "bg": "#f4f6fb",
    "kartu": "#ffffff",
    "garis": "#e5e7eb",
    "teks": "#1f2937",
    "redup": "#6b7280",
    "hover": "#f3f4f6",
    "aksen": "#3b82f6",
    "benar": "#22c55e",
    "benar_muda": "#dcfce7",
    "salah": "#ef4444",
    "salah_muda": "#fee2e2",
    "oranye": "#f59e0b",
}


def campur(warna_a, warna_b, t):
    """Campur dua warna hex. t=0 memberi warna_a, t=1 memberi warna_b."""
    a = [int(warna_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(warna_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class QuizApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Quiz Interaktif - Tugas Akhir")
        self.window.geometry("700x640")
        self.window.minsize(700, 640)
        self.window.configure(bg=WARNA["bg"])

        # Data quiz
        self.questions = [
            {
                "question": "Apa itu event-driven programming?",
                "options": ["Program yang berjalan berurutan", "Program yang merespons kejadian",
                            "Program tanpa GUI", "Program berbasis web"],
                "correct": 1,
            },
            {
                "question": "Method apa yang memulai event loop pada jendela Tkinter?",
                "options": ["mainloop()", "start()", "run()", "execute()"],
                "correct": 0,
            },
            {
                "question": "Widget mana yang cocok untuk memilih satu jawaban dari beberapa opsi?",
                "options": ["Checkbutton", "Radiobutton", "Scale", "Spinbox"],
                "correct": 1,
            },
            {
                "question": "Method mana yang menjadwalkan fungsi berjalan setelah jeda tanpa membekukan GUI?",
                "options": ["after()", "sleep()", "delay()", "wait()"],
                "correct": 0,
            },
            {
                "question": "Mengapa time.sleep() bermasalah di program GUI?",
                "options": ["Membuat memori penuh", "Memblokir event loop sehingga jendela membeku",
                            "Menghapus semua widget", "Tidak tersedia di Python 3"],
                "correct": 1,
            },
            {
                "question": "Method mana yang mengikat sebuah event ke fungsi handler?",
                "options": ["connect()", "bind()", "attach()", "listen()"],
                "correct": 1,
            },
            {
                "question": "Pola event Tkinter untuk menekan tombol Enter adalah:",
                "options": ["<Enter>", "<Return>", "<Submit>", "<Key-Go>"],
                "correct": 1,
            },
            {
                "question": "Variabel kontrol mana yang menyimpan angka bulat untuk Radiobutton?",
                "options": ["IntVar", "ListVar", "BoolArray", "ValueBox"],
                "correct": 0,
            },
            {
                "question": "Geometry manager mana yang menyusun widget dalam baris dan kolom?",
                "options": ["pack()", "grid()", "place()", "side()"],
                "correct": 1,
            },
            {
                "question": "Fungsi handler yang didaftarkan lewat bind() menerima argumen apa?",
                "options": ["Objek event berisi info kejadian", "Tidak ada argumen",
                            "Nama widget saja", "Daftar semua widget"],
                "correct": 0,
            },
        ]

        # State management
        self.current_question = 0
        self.score = 0
        self.time_left = WAKTU_PER_SOAL
        self.selected_answer = tk.IntVar(value=-1)
        self.acak = tk.BooleanVar(value=True)
        self.order = list(range(len(self.questions)))  # urutan soal
        self.perm = [0, 1, 2, 3]                       # urutan opsi soal aktif
        self.results = []                              # hasil per soal yang sudah selesai
        self.tahap = "mulai"                           # mulai | menjawab | feedback | hasil

        self.deadline = 0.0
        self.timer_job = None
        self.job_peringatan = None
        self.anim_jobs = []
        self.timer_style = None
        self.frame_hasil = None

        self.buat_interface()
        self.tampil_mulai()

        self.window.bind("<Return>", self.on_enter)
        self.window.bind("<Escape>", self.on_escape)
        self.window.bind("<Key>", self.on_key)
        self.window.protocol("WM_DELETE_WINDOW", self.keluar)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def buat_interface(self):
        w = WARNA
        style = ttk.Style(self.window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        for nama, warna in (("Progress", w["aksen"]), ("Hijau", w["benar"]),
                            ("Oranye", w["oranye"]), ("Merah", w["salah"])):
            style.configure(f"{nama}.Horizontal.TProgressbar", troughcolor=w["garis"],
                            background=warna, bordercolor=w["garis"],
                            lightcolor=warna, darkcolor=warna, thickness=12)

        self.buat_layar_mulai()
        self.buat_layar_quiz()

    def buat_layar_mulai(self):
        w = WARNA
        f = self.frame_mulai = tk.Frame(self.window, bg=w["bg"])
        tk.Label(f, text="Quiz Interaktif", font=(FONT, 30, "bold"),
                 bg=w["bg"], fg=w["teks"]).pack(pady=(70, 6))
        tk.Label(f, text=f"{len(self.questions)} soal  |  {WAKTU_PER_SOAL} detik per soal  |  "
                         f"{POIN_BENAR} poin per jawaban benar",
                 font=(FONT, 11), bg=w["bg"], fg=w["redup"]).pack()

        kartu = tk.Frame(f, bg=w["kartu"], highlightbackground=w["garis"], highlightthickness=1)
        kartu.pack(pady=26, ipadx=24, ipady=10)
        tk.Label(kartu, text="Pintasan keyboard", font=(FONT, 11, "bold"),
                 bg=w["kartu"], fg=w["teks"]).pack(pady=(10, 4))
        for baris in ("1 - 4      pilih jawaban", "Enter      kirim jawaban / lanjut",
                      "Esc        lewati soal"):
            tk.Label(kartu, text=baris, font=("Courier", 11), bg=w["kartu"],
                     fg=w["redup"], anchor="w").pack(anchor="w", padx=24)

        tk.Checkbutton(f, text="Acak urutan soal dan opsi", variable=self.acak,
                       font=(FONT, 11), bg=w["bg"], fg=w["teks"], activebackground=w["bg"],
                       cursor="hand2").pack(pady=(0, 14))

        self.btn_mulai = tk.Button(f, text="Mulai Quiz Baru", font=(FONT, 13, "bold"),
                                   bg=w["aksen"], fg="white", activebackground="#2563eb",
                                   activeforeground="white", relief="flat", padx=26, pady=8,
                                   cursor="hand2", command=self.mulai_baru)
        self.btn_mulai.pack()
        self.btn_lanjut = tk.Button(f, text="", font=(FONT, 12), bg=w["kartu"], fg=w["teks"],
                                    relief="solid", bd=1, padx=20, pady=6, cursor="hand2",
                                    command=self.lanjutkan)

    def buat_layar_quiz(self):
        w = WARNA
        n = len(self.questions)
        fq = self.frame_quiz = tk.Frame(self.window, bg=w["bg"])

        head = tk.Frame(fq, bg=w["bg"])
        head.pack(fill="x", padx=24, pady=(16, 4))
        self.lbl_nomor = tk.Label(head, text="", font=(FONT, 12, "bold"), bg=w["bg"], fg=w["teks"])
        self.lbl_nomor.pack(side="left")
        self.lbl_skor = tk.Label(head, text="Skor: 0", font=(FONT, 16, "bold"),
                                 bg=w["bg"], fg=w["aksen"])
        self.lbl_skor.pack(side="right")

        self.pb_progress = ttk.Progressbar(fq, style="Progress.Horizontal.TProgressbar",
                                           maximum=n, mode="determinate")
        self.pb_progress.pack(fill="x", padx=24)
        self.lbl_progress = tk.Label(fq, text="", font=(FONT, 9), bg=w["bg"], fg=w["redup"], anchor="e")
        self.lbl_progress.pack(fill="x", padx=24)

        trow = tk.Frame(fq, bg=w["bg"])
        trow.pack(fill="x", padx=24, pady=(4, 0))
        self.lbl_timer = tk.Label(trow, text="", font=(FONT, 12, "bold"), width=12,
                                  anchor="w", bg=w["bg"], fg=w["benar"])
        self.lbl_timer.pack(side="left")
        self.pb_timer = ttk.Progressbar(trow, style="Hijau.Horizontal.TProgressbar",
                                        maximum=WAKTU_PER_SOAL, mode="determinate")
        self.pb_timer.pack(side="left", fill="x", expand=True)

        card = tk.Frame(fq, bg=w["kartu"], highlightbackground=w["garis"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=12)
        self.lbl_pertanyaan = tk.Label(card, text="", font=(FONT, 15, "bold"), bg=w["kartu"],
                                       fg=w["teks"], wraplength=600, justify="left", anchor="w")
        self.lbl_pertanyaan.pack(fill="x", padx=20, pady=(18, 10))

        self.opsi_wrap = tk.Frame(card, bg=w["kartu"])
        self.opsi_wrap.pack(fill="x", padx=20)
        self.opsi_frames, self.opsi_radios = [], []
        for i in range(4):
            fr = tk.Frame(self.opsi_wrap, bg=w["kartu"], highlightthickness=2,
                          highlightbackground=w["kartu"], highlightcolor=w["kartu"])
            fr.pack(fill="x", pady=4)
            rb = tk.Radiobutton(fr, variable=self.selected_answer, value=i, anchor="w",
                                justify="left", wraplength=560, font=(FONT, 12),
                                bg=w["kartu"], fg=w["teks"], activebackground=w["kartu"],
                                disabledforeground=w["teks"], padx=10, pady=8, cursor="hand2",
                                command=self.on_pilih)
            rb.pack(fill="x")
            rb.bind("<Enter>", lambda e, k=i: self.on_hover(k, True))
            rb.bind("<Leave>", lambda e, k=i: self.on_hover(k, False))
            self.opsi_frames.append(fr)
            self.opsi_radios.append(rb)

        self.lbl_feedback = tk.Label(card, text="", font=(FONT, 12, "bold"), bg=w["kartu"],
                                     fg=w["teks"], wraplength=600, justify="left", anchor="w")
        self.lbl_feedback.pack(fill="x", padx=20, pady=(10, 14))

        tombol = tk.Frame(fq, bg=w["bg"])
        tombol.pack(fill="x", padx=24)
        self.btn_lewati = tk.Button(tombol, text="Lewati (Esc)", font=(FONT, 11), bg=w["kartu"],
                                    fg=w["redup"], relief="solid", bd=1, padx=16, pady=6,
                                    cursor="hand2", command=self.lewati)
        self.btn_lewati.pack(side="left")
        self.btn_submit = tk.Button(tombol, text="Kirim (Enter)", font=(FONT, 12, "bold"),
                                    bg=w["aksen"], fg="white", activebackground="#2563eb",
                                    activeforeground="white", relief="flat", padx=22, pady=7,
                                    cursor="hand2", command=self.submit_answer)
        self.btn_submit.pack(side="right")

        tk.Label(fq, text="1-4 pilih jawaban   |   Enter kirim / lanjut   |   Esc lewati",
                 font=(FONT, 9), bg=w["bg"], fg=w["redup"]).pack(pady=(8, 10))

    # ------------------------------------------------------------------
    # Navigasi layar
    # ------------------------------------------------------------------
    def tampil_mulai(self):
        self.tahap = "mulai"
        self.frame_quiz.pack_forget()
        if self.frame_hasil is not None:
            self.frame_hasil.pack_forget()
        self.frame_mulai.pack(fill="both", expand=True)
        data = self.baca_progress()
        if data:
            self.btn_lanjut.config(text=f"Lanjutkan (soal {data['current_question'] + 1} dari "
                                        f"{len(self.questions)}, skor {self.hitung_skor(data['results'])})")
            self.btn_lanjut.pack(before=self.btn_mulai, pady=(0, 10))
        else:
            self.btn_lanjut.pack_forget()

    def tampil_quiz(self):
        self.frame_mulai.pack_forget()
        if self.frame_hasil is not None:
            self.frame_hasil.pack_forget()
        self.frame_quiz.pack(fill="both", expand=True)
        self.load_question()
        self.start_timer()

    def mulai_baru(self):
        if self.baca_progress() and not messagebox.askyesno(
                "Mulai baru", "Progress yang tersimpan akan dihapus. Lanjutkan?"):
            return
        n = len(self.questions)
        self.order = list(range(n))
        if self.acak.get():
            random.shuffle(self.order)
        self.current_question = 0
        self.results = []
        self.score = 0
        self.simpan_progress()
        self.tampil_quiz()

    def lanjutkan(self):
        data = self.baca_progress()
        if not data:
            messagebox.showwarning("Progress", "Progress tersimpan tidak bisa dibaca.")
            self.tampil_mulai()
            return
        self.order = data["order"]
        self.current_question = data["current_question"]
        self.results = data["results"]
        self.score = self.hitung_skor(self.results)
        self.tampil_quiz()

    # ------------------------------------------------------------------
    # Soal
    # ------------------------------------------------------------------
    def load_question(self):
        w = WARNA
        self.batal_animasi()
        self.batal_peringatan()
        q = self.questions[self.order[self.current_question]]
        jumlah_opsi = len(q["options"])
        self.perm = random.sample(range(jumlah_opsi), jumlah_opsi) if self.acak.get() \
            else list(range(jumlah_opsi))

        self.tahap = "menjawab"
        self.selected_answer.set(-1)
        self.opsi_wrap.pack_configure(padx=20)
        self.lbl_pertanyaan.config(text=q["question"])
        for i in range(4):
            fr, rb = self.opsi_frames[i], self.opsi_radios[i]
            if i < jumlah_opsi:
                rb.config(text=f"{chr(65 + i)}.   {q['options'][self.perm[i]]}", state="normal")
                self.set_warna_opsi(i, w["kartu"], w["kartu"])
                if not fr.winfo_manager():
                    fr.pack(fill="x", pady=4)
            else:
                fr.pack_forget()

        self.lbl_feedback.config(text="", fg=w["teks"])
        self.btn_submit.config(text="Kirim (Enter)")
        self.btn_lewati.config(state="normal")
        self.lbl_skor.config(text=f"Skor: {self.score}", font=(FONT, 16, "bold"), fg=w["aksen"])
        self.lbl_nomor.config(text=f"Soal {self.current_question + 1} dari {len(self.questions)}")
        self.pb_progress["value"] = self.current_question
        self.lbl_progress.config(text=f"{self.current_question} soal selesai")

    def set_warna_opsi(self, i, warna, garis=None):
        garis = garis or warna
        self.opsi_frames[i].config(bg=warna, highlightbackground=garis, highlightcolor=garis)
        self.opsi_radios[i].config(bg=warna, activebackground=warna)

    def refresh_seleksi(self):
        w = WARNA
        pilihan = self.selected_answer.get()
        for i in range(len(self.opsi_frames)):
            garis = w["aksen"] if i == pilihan else w["kartu"]
            self.set_warna_opsi(i, w["kartu"], garis)

    def on_pilih(self):
        if self.tahap != "menjawab":
            return
        self.refresh_seleksi()
        self.batal_peringatan()
        self.lbl_feedback.config(text="")

    def on_hover(self, i, masuk):
        if self.tahap != "menjawab" or self.selected_answer.get() == i:
            return
        warna = WARNA["hover"] if masuk else WARNA["kartu"]
        self.set_warna_opsi(i, warna, warna)

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------
    def start_timer(self):
        self.hentikan_timer()
        self.time_left = WAKTU_PER_SOAL
        self.timer_style = None
        self.deadline = time.monotonic() + WAKTU_PER_SOAL
        self._tick()

    def hentikan_timer(self):
        if self.timer_job is not None:
            self.window.after_cancel(self.timer_job)
            self.timer_job = None

    def _tick(self):
        sisa = self.deadline - time.monotonic()
        if sisa <= 0:
            self.time_left = 0
            self.update_timer_ui(0)
            self.timer_job = None
            self.waktu_habis()
            return
        self.time_left = math.ceil(sisa)
        self.update_timer_ui(sisa)
        self.timer_job = self.window.after(100, self._tick)

    def update_timer_ui(self, sisa):
        w = WARNA
        if self.time_left > 10:
            nama, warna = "Hijau", w["benar"]
        elif self.time_left > 5:
            nama, warna = "Oranye", w["oranye"]
        else:
            nama, warna = "Merah", w["salah"]
        if nama != self.timer_style:
            self.pb_timer.config(style=f"{nama}.Horizontal.TProgressbar")
            self.timer_style = nama
        if self.time_left <= 5 and int(sisa * 2) % 2 == 1:
            warna = w["teks"]  # berkedip di 5 detik terakhir
        self.lbl_timer.config(text=f"Waktu: {self.time_left} dtk", fg=warna)
        self.pb_timer["value"] = sisa

    # ------------------------------------------------------------------
    # Jawaban
    # ------------------------------------------------------------------
    def submit_answer(self, event=None):
        if self.tahap == "feedback":
            self.lanjut()
            return
        if self.tahap != "menjawab":
            return

        pilihan = self.selected_answer.get()
        if pilihan == -1:  # validasi: wajib memilih
            self.tampil_peringatan("Pilih salah satu jawaban sebelum mengirim.")
            self.getar(self.opsi_wrap)
            return

        self.hentikan_timer()
        q = self.questions[self.order[self.current_question]]
        benar_idx = self.perm.index(q["correct"])
        benar = pilihan == benar_idx
        teks_pilihan = q["options"][self.perm[pilihan]]
        self.catat("benar" if benar else "salah", teks_pilihan)

        if benar:
            self.score += POIN_BENAR
            self.sorot(pilihan, "benar")
            self.tampil_feedback(f"Benar! +{POIN_BENAR} poin", WARNA["benar"])
            self.denyut_skor()
        else:
            self.sorot(pilihan, "salah")
            self.window.after(350, lambda: self.sorot(benar_idx, "benar"))
            self.getar(self.opsi_wrap)
            self.tampil_feedback(f"Salah. Jawaban benar: {chr(65 + benar_idx)}. "
                                 f"{q['options'][q['correct']]}", WARNA["salah"])
        self.masuk_feedback()

    def waktu_habis(self):
        if self.tahap != "menjawab":
            return
        q = self.questions[self.order[self.current_question]]
        benar_idx = self.perm.index(q["correct"])
        self.catat("waktu habis", None)
        self.sorot(benar_idx, "benar")
        self.getar(self.opsi_wrap)
        self.tampil_feedback(f"Waktu habis. Jawaban benar: {chr(65 + benar_idx)}. "
                             f"{q['options'][q['correct']]}", WARNA["salah"])
        self.masuk_feedback()

    def lewati(self, event=None):
        if self.tahap != "menjawab":
            return
        self.hentikan_timer()
        self.catat("lewati", None)
        self.lanjut()

    def catat(self, status, teks_pilihan):
        self.results.append({"q": self.order[self.current_question],
                             "status": status, "pilihan": teks_pilihan})

    def masuk_feedback(self):
        self.tahap = "feedback"
        for rb in self.opsi_radios:
            rb.config(state="disabled")
        self.btn_lewati.config(state="disabled")
        terakhir = self.current_question + 1 >= len(self.questions)
        self.btn_submit.config(text="Lihat Hasil (Enter)" if terakhir else "Lanjut (Enter)")
        self.lbl_skor.config(text=f"Skor: {self.score}")
        self.animasi_bar(self.pb_progress, self.current_question + 1)
        self.lbl_progress.config(text=f"{self.current_question + 1} soal selesai")

    def lanjut(self):
        self.current_question += 1
        if self.current_question >= len(self.questions):
            self.show_result()
            return
        self.simpan_progress()
        self.load_question()
        self.start_timer()

    # ------------------------------------------------------------------
    # Animasi
    # ------------------------------------------------------------------
    def batal_animasi(self):
        for job in self.anim_jobs:
            self.window.after_cancel(job)
        self.anim_jobs = []

    def animasi_warna(self, setter, awal, akhir, langkah=12, jeda=22):
        def step(n):
            setter(campur(awal, akhir, n / langkah))
            if n < langkah:
                self.anim_jobs.append(self.window.after(jeda, lambda: step(n + 1)))
        step(0)

    def sorot(self, i, jenis):
        w = WARNA
        muda, tua = (w["benar_muda"], w["benar"]) if jenis == "benar" else (w["salah_muda"], w["salah"])
        self.opsi_frames[i].config(highlightbackground=tua, highlightcolor=tua)
        self.animasi_warna(lambda c: self.set_warna_opsi(i, c, tua), w["kartu"], muda)

    def getar(self, widget):
        geser = [-10, 10, -8, 8, -5, 5, -2, 2, 0]

        def step(k):
            dx = geser[k]
            widget.pack_configure(padx=(20 + dx, 20 - dx))
            if k < len(geser) - 1:
                self.anim_jobs.append(self.window.after(28, lambda: step(k + 1)))
        step(0)

    def denyut_skor(self):
        ukuran = [18, 21, 24, 21, 18, 16]

        def step(k):
            self.lbl_skor.config(font=(FONT, ukuran[k], "bold"), text=f"Skor: {self.score}")
            if k < len(ukuran) - 1:
                self.anim_jobs.append(self.window.after(45, lambda: step(k + 1)))
        step(0)

    def animasi_bar(self, bar, target, langkah=10, jeda=20):
        awal = float(bar["value"])

        def step(n):
            bar["value"] = awal + (target - awal) * n / langkah
            if n < langkah:
                self.anim_jobs.append(self.window.after(jeda, lambda: step(n + 1)))
        step(0)

    def tampil_feedback(self, teks, warna):
        self.batal_peringatan()
        self.lbl_feedback.config(text=teks, fg=warna)

    def tampil_peringatan(self, teks):
        self.batal_peringatan()
        self.lbl_feedback.config(text=teks, fg=WARNA["oranye"])
        self.job_peringatan = self.window.after(2500, self.hapus_peringatan)

    def hapus_peringatan(self):
        self.job_peringatan = None
        if self.tahap == "menjawab":
            self.lbl_feedback.config(text="")

    def batal_peringatan(self):
        if self.job_peringatan is not None:
            self.window.after_cancel(self.job_peringatan)
            self.job_peringatan = None

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------
    def on_enter(self, event):
        if self.tahap in ("menjawab", "feedback"):
            self.submit_answer()

    def on_escape(self, event):
        if self.tahap == "menjawab":
            self.lewati()

    def on_key(self, event):
        if self.tahap == "menjawab" and event.char in ("1", "2", "3", "4"):
            i = int(event.char) - 1
            if i < len(self.questions[self.order[self.current_question]]["options"]):
                self.selected_answer.set(i)
                self.on_pilih()

    # ------------------------------------------------------------------
    # Hasil
    # ------------------------------------------------------------------
    def show_result(self):
        w = WARNA
        self.tahap = "hasil"
        self.hentikan_timer()
        self.batal_animasi()
        self.batal_peringatan()
        self.hapus_progress()
        self.score = self.hitung_skor(self.results)
        self.frame_quiz.pack_forget()
        if self.frame_hasil is not None:
            self.frame_hasil.destroy()

        total = len(self.questions)
        maks = total * POIN_BENAR
        persen = round(self.score / maks * 100)
        hitung = {s: sum(1 for r in self.results if r["status"] == s)
                  for s in ("benar", "salah", "lewati", "waktu habis")}
        if persen >= 90:
            nilai = "Luar biasa"
        elif persen >= 70:
            nilai = "Bagus"
        elif persen >= 50:
            nilai = "Cukup"
        else:
            nilai = "Perlu latihan lagi"

        f = self.frame_hasil = tk.Frame(self.window, bg=w["bg"])
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Quiz Selesai", font=(FONT, 22, "bold"), bg=w["bg"],
                 fg=w["teks"]).pack(pady=(20, 0))
        lbl_angka = tk.Label(f, text="0", font=(FONT, 48, "bold"), bg=w["bg"], fg=w["aksen"])
        lbl_angka.pack()
        tk.Label(f, text=f"dari {maks} poin  |  {nilai}", font=(FONT, 12), bg=w["bg"],
                 fg=w["redup"]).pack()

        bar = ttk.Progressbar(f, style="Progress.Horizontal.TProgressbar", maximum=maks, length=420)
        bar.pack(pady=10)
        self.animasi_hitung(lbl_angka, bar, self.score)

        stat = tk.Frame(f, bg=w["bg"])
        stat.pack(pady=(0, 8))
        for teks, kunci, warna in (("Benar", "benar", w["benar"]), ("Salah", "salah", w["salah"]),
                                   ("Dilewati", "lewati", w["redup"]),
                                   ("Waktu habis", "waktu habis", w["oranye"])):
            kolom = tk.Frame(stat, bg=w["bg"])
            kolom.pack(side="left", padx=16)
            tk.Label(kolom, text=str(hitung[kunci]), font=(FONT, 18, "bold"),
                     bg=w["bg"], fg=warna).pack()
            tk.Label(kolom, text=teks, font=(FONT, 10), bg=w["bg"], fg=w["redup"]).pack()

        box = tk.Frame(f, bg=w["kartu"], highlightbackground=w["garis"], highlightthickness=1)
        box.pack(fill="both", expand=True, padx=24, pady=6)
        scroll = tk.Scrollbar(box)
        scroll.pack(side="right", fill="y")
        teks = tk.Text(box, wrap="word", font=(FONT, 10), bg=w["kartu"], fg=w["teks"],
                       relief="flat", padx=12, pady=8, yscrollcommand=scroll.set, height=8)
        teks.pack(fill="both", expand=True)
        scroll.config(command=teks.yview)
        teks.tag_config("benar", foreground=w["benar"], font=(FONT, 10, "bold"))
        teks.tag_config("salah", foreground=w["salah"], font=(FONT, 10, "bold"))
        teks.tag_config("lewati", foreground=w["redup"], font=(FONT, 10, "bold"))
        teks.tag_config("redup", foreground=w["redup"])
        label = {"benar": "BENAR", "salah": "SALAH", "lewati": "DILEWATI", "waktu habis": "WAKTU HABIS"}
        for no, r in enumerate(self.results, 1):
            q = self.questions[r["q"]]
            tag = "benar" if r["status"] == "benar" else ("salah" if r["status"] == "salah" else "lewati")
            teks.insert("end", f"{no}. {label[r['status']]}\n", tag)
            teks.insert("end", f"{q['question']}\n")
            if r["status"] != "benar":
                teks.insert("end", f"Jawabanmu: {r['pilihan'] or '(kosong)'}\n", "redup")
            teks.insert("end", f"Jawaban benar: {q['options'][q['correct']]}\n\n", "redup")
        teks.config(state="disabled")

        tombol = tk.Frame(f, bg=w["bg"])
        tombol.pack(pady=(6, 14))
        tk.Button(tombol, text="Ulangi Quiz", font=(FONT, 12, "bold"), bg=w["aksen"], fg="white",
                  activebackground="#2563eb", activeforeground="white", relief="flat",
                  padx=20, pady=6, cursor="hand2", command=self.tampil_mulai).pack(side="left", padx=6)
        tk.Button(tombol, text="Keluar", font=(FONT, 12), bg=w["kartu"], fg=w["teks"],
                  relief="solid", bd=1, padx=20, pady=6, cursor="hand2",
                  command=self.window.destroy).pack(side="left", padx=6)

    def animasi_hitung(self, label, bar, target, langkah=30, jeda=30):
        def step(n):
            nilai = round(target * n / langkah)
            label.config(text=str(nilai))
            bar["value"] = nilai
            if n < langkah:
                self.anim_jobs.append(self.window.after(jeda, lambda: step(n + 1)))
        step(0)

    # ------------------------------------------------------------------
    # Penyimpanan state
    # ------------------------------------------------------------------
    @staticmethod
    def hitung_skor(results):
        return POIN_BENAR * sum(1 for r in results if r["status"] == "benar")

    def simpan_progress(self):
        data = {"order": self.order, "current_question": self.current_question,
                "score": self.score, "results": self.results}
        try:
            with open(FILE_PROGRESS, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def baca_progress(self):
        try:
            with open(FILE_PROGRESS, encoding="utf-8") as f:
                data = json.load(f)
            n = len(self.questions)
            ok = (sorted(data["order"]) == list(range(n))
                  and isinstance(data["current_question"], int)
                  and 0 <= data["current_question"] < n
                  and len(data["results"]) == data["current_question"]
                  and all(r["status"] in ("benar", "salah", "lewati", "waktu habis")
                          and r["q"] in data["order"] for r in data["results"]))
            return data if ok else None
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def hapus_progress(self):
        try:
            os.remove(FILE_PROGRESS)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def keluar(self):
        if self.tahap in ("menjawab", "feedback"):
            if not messagebox.askyesno("Keluar", "Progress tersimpan sampai soal ini. Keluar sekarang?"):
                return
            self.hentikan_timer()
            if self.tahap == "feedback":
                self.current_question += 1
            if self.current_question >= len(self.questions):
                self.hapus_progress()
            else:
                self.simpan_progress()
        self.window.destroy()

    def jalankan(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = QuizApp()
    app.jalankan()