import tkinter as tk
from datetime import datetime


def update_time():
    clock.config(text=datetime.now().strftime("%H:%M:%S"))
    window.after(1000, update_time)


def toggle_always_on_top():
    always_on_top = not window.attributes("-topmost")
    window.attributes("-topmost", always_on_top)
    pin_button.config(text=f"항상 위에 표시: {'켬' if always_on_top else '끔'}")
    if always_on_top:
        window.lift()


window = tk.Tk()
window.title("현재 시간")
clock = tk.Label(window, font=("Arial", 48), padx=24, pady=16)
clock.pack()
pin_button = tk.Button(
    window,
    text="항상 위에 표시: 끔",
    command=toggle_always_on_top,
)
pin_button.pack(pady=(0, 16))
update_time()
window.mainloop()
