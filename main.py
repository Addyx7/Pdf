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

# ---------------- CONFIG ----------------

UPDATE_INDEX_URL = "https://pastebin.com/raw/MR1G7jvS"

# iOS-style colors
COLOR_BG = "#F2F2F7"
COLOR_CARD = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#000000"
COLOR_TEXT_SECONDARY = "#8E8E93"
COLOR_ACCENT = "#007AFF"
COLOR_ERROR = "#FF3B30"


# ---------------- UI COMPONENT ----------------

class IOSCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = [26, 26, 26, 26]
        self.spacing = 12

        with self.canvas.before:
            Color(0, 0, 0, 0.12)
            BoxShadow(
                pos=self.pos,
                size=self.size,
                offset=(0, -10),
                blur_radius=40,
                border_radius=[26] * 4
            )
            Color(*get_color_from_hex(COLOR_CARD))
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[26]
            )

        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ---------------- MAIN APP ----------------

class PDFViewerApp(App):

    def build(self):
        Window.clearcolor = get_color_from_hex(COLOR_BG)

        root = FloatLayout()

        self.card = IOSCard(
            orientation="vertical",
            size_hint=(None, None),
            size=(330, 240),
        )
        self.card.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.card.opacity = 0

        self.title = Label(
            text="PDF Viewer",
            font_size="20sp",
            bold=True,
            color=get_color_from_hex(COLOR_TEXT_PRIMARY),
            size_hint_y=None,
            height=36
        )

        self.subtitle = Label(
            text="Preparing document…",
            font_size="14sp",
            color=get_color_from_hex(COLOR_TEXT_SECONDARY),
            size_hint_y=None,
            height=28
        )

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=10
        )
        self.progress.opacity = 0

        self.retry = Button(
            text="Try Again",
            size_hint_y=None,
            height=40,
            background_normal="",
            background_color=get_color_from_hex(COLOR_ACCENT),
        )
        self.retry.opacity = 0
        self.retry.disabled = True
        self.retry.bind(on_release=self.restart)

        self.card.add_widget(self.title)
        self.card.add_widget(self.subtitle)
        self.card.add_widget(self.progress)
        self.card.add_widget(self.retry)

        root.add_widget(self.card)

        Animation(opacity=1, duration=0.6, t="out_cubic").start(self.card)
        Clock.schedule_once(self.start_flow, 1)

        return root

    # ---------------- UI HELPERS ----------------

    def set_ui(self, title, subtitle, progress=None, error=False):
        self.title.text = title
        self.subtitle.text = subtitle
        self.title.color = get_color_from_hex(
            COLOR_ERROR if error else COLOR_TEXT_PRIMARY
        )

        if progress is None:
            Animation(opacity=0, duration=0.25).start(self.progress)
        else:
            Animation(opacity=1, duration=0.25).start(self.progress)
            Animation(value=progress, duration=0.25).start(self.progress)

    def show_retry(self):
        self.retry.disabled = False
        Animation(opacity=1, duration=0.3).start(self.retry)

    def restart(self, *_):
        self.retry.disabled = True
        Animation(opacity=0, duration=0.3).start(self.retry)
        self.start_flow(0)

    # ---------------- FLOW ----------------

    def start_flow(self, _):
        self.set_ui("Opening PDF", "Loading file…")
        threading.Thread(target=self.load_update_index, daemon=True).start()

    def load_update_index(self):
        try:
            r = requests.get(UPDATE_INDEX_URL, timeout=6)
            self.update_index = {}
            for pair in r.text.replace("\n", ",").split(","):
                if "=" in pair:
                    h, u = pair.split("=", 1)
                    self.update_index[h.strip()] = u.strip()
        except Exception:
            self.update_index = {}

        Clock.schedule_once(lambda dt: self.handle_intent(), 0)

    def handle_intent(self):
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            intent = activity.getIntent()
            uri = intent.getData()

            if not uri:
                self.set_ui("PDF Viewer", "No document selected")
                return

            self.set_ui("Preparing PDF", "Reading document…")
            threading.Thread(
                target=self.compute_hash,
                args=(activity, uri),
                daemon=True
            ).start()

        except Exception:
            self.set_ui("Error", "Unable to open file", error=True)

    def compute_hash(self, activity, uri):
        try:
            resolver = activity.getContentResolver()
            stream = resolver.openInputStream(uri)

            digest = hashlib.sha256()
            buf = bytearray(1024 * 1024)

            while True:
                n = stream.read(buf)
                if n == -1:
                    break
                digest.update(buf[:n])

            file_hash = digest.hexdigest()

            Clock.schedule_once(
                lambda dt: self.resolve_pdf(file_hash, uri, activity),
                0
            )

        except Exception:
            Clock.schedule_once(
                lambda dt: self.set_ui(
                    "Error", "File could not be read", error=True
                ),
                0
            )

    def resolve_pdf(self, file_hash, original_uri, activity):
        if file_hash in self.update_index:
            url = self.update_index[file_hash]
            base = activity.getExternalFilesDir(None).getAbsolutePath()
            local = os.path.join(base, f"cached_{file_hash[:8]}.pdf")

            if os.path.exists(local):
                self.open_pdf(local, activity)
            else:
                self.download_pdf(url, local, activity)
        else:
            self.set_ui("Opening PDF", "Rendering document…")
            self.open_original(original_uri, activity)

    # ---------------- DOWNLOAD ----------------

    def download_pdf(self, url, path, activity):
        self.set_ui("Downloading", "Fetching latest version…", 0)
        threading.Thread(
            target=self._download,
            args=(url, path, activity),
            daemon=True
        ).start()

    def _download(self, url, path, activity):
        try:
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        downloaded += len(chunk)
                        f.write(chunk)
                        if total:
                            p = int(downloaded / total * 100)
                            Clock.schedule_once(
                                lambda dt, p=p: self.set_ui(
                                    "Downloading",
                                    "Fetching latest version…",
                                    p
                                ),
                                0
                            )

            Clock.schedule_once(
                lambda dt: self.open_pdf(path, activity),
                0
            )

        except Exception:
            Clock.schedule_once(
                lambda dt: self.set_ui(
                    "Download Failed",
                    "Check your connection",
                    error=True
                ),
                0
            )
            Clock.schedule_once(lambda dt: self.show_retry(), 0)

    # ---------------- OPENERS ----------------

    def open_pdf(self, path, activity):
        self.set_ui("Opening PDF", "Launching viewer…")

        Intent = autoclass("android.content.Intent")
        File = autoclass("java.io.File")
        FileProvider = autoclass("androidx.core.content.FileProvider")

        context = activity.getApplicationContext()
        pkg = context.getPackageName()

        file_obj = File(path)
        uri = FileProvider.getUriForFile(
            context, f"{pkg}.fileprovider", file_obj
        )

        view = Intent(Intent.ACTION_VIEW)
        view.setDataAndType(uri, "application/pdf")
        view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        activity.startActivity(view)
        activity.finish()

    def open_original(self, uri, activity):
        Intent = autoclass("android.content.Intent")
        view = Intent(Intent.ACTION_VIEW)
        view.setDataAndType(uri, "application/pdf")
        view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        activity.startActivity(view)
        activity.finish()


if __name__ == "__main__":
    PDFViewerApp().run()
