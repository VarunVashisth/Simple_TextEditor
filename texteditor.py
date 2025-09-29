# text_editor_standalone.py
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import fitz
import io
import os
import shutil

class TextEditorStandalone:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Text Editor")
        self.root.geometry("1200x700")
        self.current_file = None
        self.embedded_media = []
        self.create_ui()
        self.bind_hotkeys()
        self.root.mainloop()

    def create_ui(self):
        toolbar = tk.Frame(self.root, bg='#222222', relief='flat', bd=0, highlightthickness=0)
        toolbar.pack(side='top', fill='x', padx=0, pady=0)

        btn_style = {'bg':'#222222','fg':'#cccccc','activebackground':'#333333','activeforeground':'#ffffff',
                     'relief':'flat','bd':0,'font':('Segoe UI',10),'highlightthickness':0,'padx':12,'pady':6,'cursor':'hand2'}

        # Toolbar buttons
        tk.Button(toolbar, text="Heading", command=self.make_heading, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Subheading", command=self.make_subheading, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Normal", command=self.make_normal, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Underline", command=self.make_underline, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Insert Image", command=self.upload_image, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Insert Video", command=self.insert_video_embed, **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Insert PDF", command=lambda: self.insert_media([("PDF files","*.pdf")],"PDF"), **btn_style).pack(side='left', padx=0)
        tk.Button(toolbar, text="Insert Docs", command=lambda: self.insert_media([("Word files","*.doc *.docx")],"DOC"), **btn_style).pack(side='left', padx=0)

        # --- Text Area below toolbar ---
        self.text_area = tk.Text(
            self.root,
            bg='#1a1a1a',
            fg='#e0e0e0',
            insertbackground='#ffffff',
            selectbackground='#404040',
            selectforeground='#ffffff',
            font=('Consolas', 12),
            wrap='word',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.text_area.pack(side='top', fill='both', expand=True)
    def bind_hotkeys(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-S>', lambda e: self.save_as_file())
        self.text_area.bind('<Control-a>', self.select_all)
        self.text_area.bind('<Control-b>', self.make_bold)
        self.text_area.bind('<Control-u>', self.make_underline)
        self.text_area.bind('<Control-1>', self.make_heading)
        self.text_area.bind('<Control-2>', self.make_subheading)
        self.text_area.bind('<Control-3>', self.make_normal)

    # Formatting functions
    def select_all(self, event=None):
        self.text_area.tag_add('sel','1.0','end-1c')
        return 'break'

    def make_bold(self, event=None):
        self.toggle_tag('bold')
        return 'break'

    def make_underline(self, event=None):
        self.toggle_tag('underline')
        return 'break'

    def make_heading(self, event=None):
        self.replace_tags(['subheading','normal'],'heading')
        return 'break'

    def make_subheading(self, event=None):
        self.replace_tags(['heading','normal'],'subheading')
        return 'break'

    def make_normal(self, event=None):
        self.replace_tags(['heading','subheading'],'normal')
        return 'break'

    def toggle_tag(self, tag):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
            if tag in self.text_area.tag_names('sel.first'):
                self.text_area.tag_remove(tag,start,end)
            else:
                self.text_area.tag_add(tag,start,end)
        except tk.TclError:
            pass

    def replace_tags(self, remove_tags, add_tag):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
            for t in remove_tags:
                self.text_area.tag_remove(t,start,end)
            self.text_area.tag_add(add_tag,start,end)
        except tk.TclError:
            pass

    # File operations
    def new_file(self):
        self.text_area.delete('1.0',tk.END)
        self.current_file = None

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files","*.txt")])
        if file_path:
            with open(file_path,'r',encoding='utf-8') as f:
                self.text_area.delete('1.0',tk.END)
                self.text_area.insert('1.0',f.read())
            self.current_file = file_path

    def save_file(self):
        if self.current_file:
            self.write_file(self.current_file)
        else:
            self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if file_path:
            self.write_file(file_path)
            self.current_file = file_path

    def write_file(self, path):
        with open(path,'w',encoding='utf-8') as f:
            f.write(self.text_area.get('1.0','end-1c'))

    # Media insertion
    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files","*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            try:
                img = Image.open(file_path)
                img.thumbnail((300,300))
                img_tk = ImageTk.PhotoImage(img)
                self.text_area.image_create(tk.INSERT,image=img_tk)
                self.embedded_media.append(img_tk)
            except Exception as e:
                messagebox.showerror("Error",f"Failed to insert image:\n{e}")

    def insert_video_embed(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files","*.mp4 *.avi *.mov *.mkv *.webm")])
        if not file_path:
            return
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((360,240))
                img_tk = ImageTk.PhotoImage(img)
            else:
                img_tk = None
        except:
            img_tk = None

        video_frame = tk.Frame(self.text_area, bg='#222222', bd=0)
        if img_tk:
            thumb_label = tk.Label(video_frame, image=img_tk, bg='#222222')
            thumb_label.image = img_tk
        else:
            thumb_label = tk.Label(video_frame, text="No Preview", bg='#222222', fg='#cccccc', width=66, height=21)
        thumb_label.pack(side='left')

        play_btn = tk.Button(video_frame, text="▶ Play", bg='#00bfff', fg='white', relief='flat', font=('Segoe UI',10,'bold'),
                             cursor='hand2', command=lambda: self.play_video(file_path))
        play_btn.pack(side='left', padx=8)

        download_btn = tk.Button(video_frame, text="⬇ Download", bg='#222222', fg='#00bfff', relief='flat', font=('Segoe UI',10),
                                 cursor='hand2', command=lambda: shutil.copy(file_path,filedialog.asksaveasfilename(defaultextension=".mp4")))
        download_btn.pack(side='left', padx=4)

        self.text_area.window_create(tk.INSERT, window=video_frame)

    def play_video(self, file_path):
        win = tk.Toplevel(self.root)
        win.title("Video Player")
        label = tk.Label(win)
        label.pack(fill='both', expand=True)
        cap = cv2.VideoCapture(file_path)

        vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        aspect_ratio = vid_width / vid_height

        target_width, target_height = 1280, 720
        if target_width / target_height > aspect_ratio:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        else:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)

        def show_frame():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((new_width,new_height), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                label.imgtk = img_tk
                label.config(image=img_tk)
                win.after(30, show_frame)
            else:
                cap.release()
        show_frame()
        win.protocol("WM_DELETE_WINDOW", lambda: (cap.release(), win.destroy()))

    def insert_media(self, filetypes, placeholder):
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if not file_path: return
        self.text_area.insert(tk.INSERT,f"[{placeholder}: {os.path.basename(file_path)}]\n")
        try:
            media = fitz.open(file_path)
            page = media[0]
            mat = fitz.Matrix(1.5,1.5)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img.thumbnail((300,400))
            img_tk = ImageTk.PhotoImage(img)
            media_frame = tk.Frame(self.text_area,bg='#222222')
            lbl = tk.Label(media_frame,image=img_tk,bg='#222222')
            lbl.image = img_tk
            lbl.pack(side='left')
            self.text_area.window_create(tk.INSERT,window=media_frame)
            self.embedded_media.append(img_tk)
        except:
            pass

if __name__ == "__main__":
    TextEditorStandalone()
