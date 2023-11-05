import queue
import threading
import time
import tkinter as tk
from tkinter.font import Font

from langup import base, config


def center_window(window):
    window.update_idletasks()  # 更新窗体的尺寸信息
    width = window.winfo_width()
    height = window.winfo_height()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) + 120

    window.geometry(f"{width}x{height}+{x}+{y}")


class SubtitleWindow:
    def __init__(
            self,
            subtitle_queue, text_color="#ffffff", font=("SimHei", 35, 'bolda'),
            window_width=None, window_height=600, transparent_level=0.5, bg_color="#000000"):
        """

        @param subtitle_queue:
        @param window_width:
        @param window_height:
        @param font:
        @param transparent_level:
        @param bg_color:
        @param text_color:
            "宋体" (SimSun)
            "黑体" (SimHei)
            "楷体" (KaiTi)
            "仿宋" (FangSong)
            "微软雅黑" (Microsoft YaHei)
        """
        self.subtitle_queue = subtitle_queue

        self.root = tk.Tk()
        self.root.title(f"Langup")
        self.root.attributes("-alpha", transparent_level)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", bg_color)
        self.root.overrideredirect(True)

        self.window_width = window_width or int(self.root.winfo_screenwidth()) - 300
        self.window_height = window_height

        self.canvas = tk.Canvas(self.root, width=self.window_width, height=self.window_height, bg=bg_color,
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.subtitle_list = ["Verse 1", "Chorus", "Verse 2", "Bridge", "Chorus"]
        self.current_subtitle_index = 0

        self.font = Font(family=font[0], size=int(font[1]), weight=font[2])
        self.bg_color = bg_color
        self.text_color = text_color

        self.transparent_level = transparent_level

        self.previous_x = 0
        self.previous_y = 0

        self.root.bind("<B1-Motion>", self.move_window)
        self.root.bind("<Button-1>", self.set_previous_coords)

    def set_previous_coords(self, event):
        self.previous_x = event.x
        self.previous_y = event.y

    def move_window(self, event):
        x_offset = event.x - self.previous_x
        y_offset = event.y - self.previous_y
        new_x = self.root.winfo_x() + x_offset
        new_y = self.root.winfo_y() + y_offset
        self.root.geometry(f"+{new_x}+{new_y}")

    def update_subtitle(self):
        while subtitle := self.subtitle_queue.get():
            self.display_text(subtitle, self.window_width // 2, self.window_height // 2)

    def display_text(self, text, x=10, y=50):
        self.canvas.delete('all')
        self.canvas.create_text(x, y, text=text, font=self.font, fill=self.text_color, width=self.window_width - 30)

    def stream_display_text(self, text, x=10, y=50, delay=200):
        ...

    def _start(self):
        threading.Thread(target=self.update_subtitle).start()
        center_window(self.root)
        self.root.mainloop()

    @classmethod
    def start(cls):
        subtitle_window = SubtitleWindow(subtitle_queue, **config.subtitle)
        subtitle_window._start()


subtitle_queue = queue.Queue()
subtitle_queue.put('字幕组件初始化完成')


class SubtitleReaction(base.Reaction):
    subtitle_txt: str

    async def areact(self):
        subtitle_queue.put(self.subtitle_txt)


def test_insert():
    def func():
        for i in range(100):
            time.sleep(1)
            # "insert" 索引表示插入光标当前的位置
            subtitle_queue.put(f"haha-{i}")

    threading.Thread(target=func).start()


if __name__ == '__main__':
    test_insert()
    SubtitleWindow.start()
