import threading
import hashlib
import os
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle, BoxShadow
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.animation import Animation

from jnius import autoclass

UPDATE_INDEX_URL = "https://pastebin.com/raw/MR1G7jvS"

COLOR_BG = "#F2F2F7"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#000000"
COLOR_TEXT_SECONDARY = "#8E8E93"
COLOR_ACCENT = "#007AFF"
COLOR_ERROR = "#FF3B30"


class IOSCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = 26
        self.spacing = 12

        with self.canvas.before:
            Color(0, 0, 0, 0.15)
            BoxShadow(
                pos=self.pos,
                size=self.size,
                offset=(0, -8),
                blur_radius=40,
                border_radius=[26] * 4
            )
            Color(*get_color_from_hex(COLOR_CARD))
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[26])

        self.bind(pos=self.sync, size=self.sync)

    def sync(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size


class PDFViewerApp(App):

    def build(self):
        Window.clearcolor = get_color_from_hex(COLOR_BG)

        root = FloatLayout()

        self.card = IOSCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(330, 240),
            pos_hint={"center_x": .5, "center_y": .5},
            opacity=0
        )

        self.title = Label(text="PDF Viewer", font_size="20sp", bold=True)
        self.subtitle = Label(text="Initializing…", font_size="14sp")
        self.progress = ProgressBar(max=100, value=0, opacity=0)

        self.retry = Button(
            text="Try Again",
            size_hint_y=None,
            height=42,
            background_normal="",
            background_color=get_color_from_hex(COLOR_ACCENT),
            opacity=0,
            disabled=True
        )
        self.retry.bind(on_release=self.restart)

        for w in (self.title, self.subtitle, self.progress, self.retry):
            self.card.add_widget(w)

        root.add_widget(self.card)
        Animation(opacity=1, duration=0.5).start(self.card)

        Clock.schedule_once(self.start_flow, 0.8)
        return root

    def set_ui(self, title, subtitle, progress=None, error=False):
        self.title.text = title
        self.subtitle.text = subtitle
        self.title.color = get_color_from_hex(COLOR_ERROR if error else COLOR_TEXT_PRIMARY)

        if progress is None:
            self.progress.opacity = 0
        else:
            self.progress.opacity = 1
            self.progress.value = progress

    def restart(self, *_):
        self.retry.disabled = True
        self.retry.opacity = 0
        self.start_flow(0)

    def start_flow(self, *_):
        self.set_ui("Opening PDF", "Loading…")
        threading.Thread(target=self.load_index, daemon=True).start()

    def load_index(self):
        try:
            r = requests.get(UPDATE_INDEX_URL, timeout=6)
            self.index = dict(
                p.split("=", 1) for p in r.text.replace("\n", ",").split(",") if "=" in p
            )
        except Exception:
            self.index = {}
        Clock.schedule_once(self.handle_intent, 0)

    def handle_intent(self, *_):
        try:
            Activity = autoclass("org.kivy.android.PythonActivity")
            activity = Activity.mActivity
            uri = activity.getIntent().getData()

            if not uri:
                self.set_ui("No PDF", "No file provided")
                return

            threading.Thread(
                target=self.hash_file,
                args=(activity, uri),
                daemon=True
            ).start()

        except Exception:
            self.set_ui("Error", "Intent failed", error=True)

    def hash_file(self, activity, uri):
        try:
            resolver = activity.getContentResolver()
            stream = resolver.openInputStream(uri)

            sha = hashlib.sha256()
            buf = bytearray(1024 * 1024)

            while True:
                n = stream.read(buf)
                if n == -1:
                    break
                sha.update(buf[:n])

            Clock.schedule_once(
                lambda *_: self.resolve(sha.hexdigest(), uri, activity),
                0
            )

        except Exception:
            Clock.schedule_once(
                lambda *_: self.set_ui("Error", "Read failed", error=True),
                0
            )

    def resolve(self, h, uri, activity):
        if h in self.index:
            url = self.index[h]
            base = activity.getExternalFilesDir(None).getAbsolutePath()
            path = os.path.join(base, f"{h[:8]}.pdf")

            if os.path.exists(path):
                self.open_pdf(path, activity)
            else:
                threading.Thread(
                    target=self.download,
                    args=(url, path, activity),
                    daemon=True
                ).start()
        else:
            self.open_original(uri, activity)

    def download(self, url, path, activity):
        try:
            self.set_ui("Downloading", "Fetching update…", 0)
            r = requests.get(url, stream=True, timeout=10)
            total = int(r.headers.get("content-length", 0))
            done = 0

            with open(path, "wb") as f:
                for c in r.iter_content(8192):
                    f.write(c)
                    done += len(c)
                    if total:
                        Clock.schedule_once(
                            lambda *_,
                            p=int(done / total * 100): self.set_ui(
                                "Downloading", "Fetching update…", p
                            ),
                            0
                        )

            Clock.schedule_once(lambda *_: self.open_pdf(path, activity), 0)

        except Exception:
            Clock.schedule_once(
                lambda *_: self.set_ui("Failed", "Network error", error=True),
                0
            )

    def open_pdf(self, path, activity):
        Intent = autoclass("android.content.Intent")
        File = autoclass("java.io.File")
        FileProvider = autoclass("androidx.core.content.FileProvider")

        ctx = activity.getApplicationContext()
        pkg = ctx.getPackageName()

        uri = FileProvider.getUriForFile(
            ctx, f"{pkg}.fileprovider", File(path)
        )

        i = Intent(Intent.ACTION_VIEW)
        i.setDataAndType(uri, "application/pdf")
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        activity.startActivity(i)
        activity.finish()

    def open_original(self, uri, activity):
        Intent = autoclass("android.content.Intent")
        i = Intent(Intent.ACTION_VIEW)
        i.setDataAndType(uri, "application/pdf")
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        activity.startActivity(i)
        activity.finish()


if __name__ == "__main__":
    PDFViewerApp().run()
