import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
from datetime import datetime
import winsound

class PomodoroTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("专注时钟")
        self.root.geometry("500x600")  # 初始大小
        self.root.minsize(300, 400)    # 设置最小窗口大小
        
        # 颜色主题
        self.colors = {
            'primary': '#2196F3',    # 主要按钮颜色
            'work': '#4CAF50',       # 工作时间颜色
            'break': '#FF9800',      # 休息时间颜色
            'text': '#333333',       # 文字颜色
            'bg': '#f0f0f0'          # 背景颜色
        }
        
        # 设置默认时间（以分钟为单位）
        self.work_time = 25
        self.break_time = 5
        self.long_break_time = 15
        self.pomodoro_count = 0
        
        # 计时器状态
        self.time_left = self.work_time * 60
        self.timer_running = False
        self.current_timer_thread = None
        self.current_status = "准备开始专注"
        
        self.setup_styles()
        self.setup_gui()
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure('Timer.TLabel', 
                       font=('Helvetica', 48, 'bold'),
                       foreground=self.colors['text'],
                       background=self.colors['bg'])
        
        style.configure('Status.TLabel',
                       font=('Helvetica', 14),
                       foreground=self.colors['text'],
                       background=self.colors['bg'])
        
        style.configure('Count.TLabel',
                       font=('Helvetica', 12),
                       foreground=self.colors['text'],
                       background=self.colors['bg'])
        
        style.configure('Action.TButton',
                       font=('Helvetica', 12))
        
    def setup_gui(self):
        # 配置根窗口的网格
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 主容器使用网格布局
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # 配置主框架的网格
        for i in range(6):  # 根据需要的行数调整
            main_frame.grid_rowconfigure(i, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 状态显示
        self.status_label = ttk.Label(
            main_frame,
            text=self.current_status,
            style='Status.TLabel'
        )
        self.status_label.grid(row=0, column=0, sticky="ew")
        
        # 创建画布框架
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 创建可缩放的画布
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # 绑定画布大小调整事件
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        # 时间显示标签
        self.time_label = ttk.Label(
            main_frame,
            text="25:00",
            style='Timer.TLabel',
            anchor="center"
        )
        self.time_label.grid(row=2, column=0, sticky="ew")
        
        # 番茄钟计数
        self.count_label = ttk.Label(
            main_frame,
            text="已完成番茄钟：0",
            style='Count.TLabel',
            anchor="center"
        )
        self.count_label.grid(row=3, column=0, sticky="ew")
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky="ew", pady=10)
        button_frame.grid_columnconfigure((0,1,2), weight=1)
        
        # 按钮
        self.start_button = ttk.Button(
            button_frame,
            text="开始专注",
            style='Action.TButton',
            command=self.start_timer
        )
        self.start_button.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.stop_button = ttk.Button(
            button_frame,
            text="暂停",
            style='Action.TButton',
            command=self.stop_timer,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.reset_button = ttk.Button(
            button_frame,
            text="重置",
            style='Action.TButton',
            command=self.reset_timer
        )
        self.reset_button.grid(row=0, column=2, padx=5, sticky="ew")
        
        # 提示信息
        self.tip_label = ttk.Label(
            main_frame,
            text="专注时间: 25分钟 | 短休息: 5分钟 | 长休息: 15分钟",
            style='Count.TLabel',
            anchor="center"
        )
        self.tip_label.grid(row=5, column=0, sticky="ew", pady=10)
        
        # 初始绘制进度圈
        self.draw_progress_circle()
        
    def on_canvas_resize(self, event):
        # 获取画布新的尺寸
        width = event.width
        height = event.height
        size = min(width, height) - 20  # 留出一些边距
        
        # 更新画布尺寸变量
        self.canvas_size = size
        self.circle_center = size / 2
        self.circle_radius = (size - 20) / 2  # 留出一些边距
        
        # 重绘进度圈
        self.draw_progress_circle()
        
    def draw_progress_circle(self):
        if not hasattr(self, 'canvas_size'):
            return
            
        # 清除画布
        self.canvas.delete("all")
        
        # 计算进度
        if self.current_status == "工作中":
            total_time = self.work_time * 60
        elif self.current_status == "长休息时间":
            total_time = self.long_break_time * 60
        else:
            total_time = self.break_time * 60
            
        progress = (total_time - self.time_left) / total_time if total_time > 0 else 0
        
        # 计算圆的位置
        x0 = self.circle_center - self.circle_radius
        y0 = self.circle_center - self.circle_radius
        x1 = self.circle_center + self.circle_radius
        y1 = self.circle_center + self.circle_radius
        
        # 绘制背景圆
        self.canvas.create_oval(x0, y0, x1, y1, 
                              outline=self.colors['bg'], 
                              fill=self.colors['bg'])
        
        # 绘制进度圆弧
        angle = 359.99 * progress
        if self.current_status == "工作中":
            color = self.colors['work']
        elif "休息" in self.current_status:
            color = self.colors['break']
        else:
            color = self.colors['primary']
            
        self.canvas.create_arc(x0, y0, x1, y1,
                             start=90, extent=-angle,
                             outline=color, width=max(self.circle_radius/20, 3))

    def update_timer_display(self):
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.draw_progress_circle()
        
    def timer_thread(self):
        while self.timer_running and self.time_left > 0:
            time.sleep(1)
            self.time_left -= 1
            self.root.after(0, self.update_timer_display)
            
        if self.timer_running and self.time_left <= 0:
            self.root.after(0, self.timer_complete)
            
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            if self.current_status == "准备开始专注":
                self.current_status = "工作中"
                self.status_label.config(text=self.current_status)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.current_timer_thread = threading.Thread(target=self.timer_thread)
            self.current_timer_thread.start()
            
    def stop_timer(self):
        self.timer_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def reset_timer(self):
        self.stop_timer()
        self.time_left = self.work_time * 60
        self.current_status = "准备开始专注"
        self.status_label.config(text=self.current_status)
        self.update_timer_display()
        
    def timer_complete(self):
        self.timer_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if self.current_status == "工作中":
            self.pomodoro_count += 1
            self.count_label.config(text=f"已完成番茄钟：{self.pomodoro_count}")
            
            winsound.Beep(1000, 1000)
            
            if self.pomodoro_count % 4 == 0:
                messagebox.showinfo("完成!", "太棒了! 你已经完成了4个番茄钟，现在开始长休息吧。")
                self.time_left = self.long_break_time * 60
                self.current_status = "长休息时间"
            else:
                messagebox.showinfo("完成!", "做得好! 来休息一下吧。")
                self.time_left = self.break_time * 60
                self.current_status = "休息时间"
        else:
            messagebox.showinfo("休息结束", "休息结束了，让我们开始新的专注时间吧！")
            self.time_left = self.work_time * 60
            self.current_status = "工作中"
            
        self.status_label.config(text=self.current_status)
        self.update_timer_display()
        
    def run(self):
        try:
            self.root.iconbitmap('clock.ico')
        except:
            pass
        self.root.mainloop()

if __name__ == "__main__":
    app = PomodoroTimer()
    app.run()