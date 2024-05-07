import tkinter as tk
from tkinter import ttk, Menu, simpledialog
import pandas as pd
from VideoData import VideoData
import pyperclip
from utils import extract_speaker_name
from PIL import Image, ImageTk
import os
from playsound import playsound
import threading

import tkinter.filedialog as filedialog

# Function to handle button click and open directory dialog
def open_directory_dialog(entry_widget, default_path = None):
    if default_path is None:
        default_path = os.getcwd()
    folder_path = filedialog.askdirectory(initialdir=default_path)
    if folder_path:
        entry_widget.delete(0, tk.END)  # Clear current content
        entry_widget.insert(0, folder_path)  # Insert selected folder path

def open_directory_dialog_and_scan(entry_widget, listbox, default_path=None):
    if default_path is None:
        default_path = os.getcwd()
    folder_path = filedialog.askdirectory(initialdir=default_path)
    if folder_path:
        entry_widget.delete(0, tk.END)  # Clear current content
        entry_widget.insert(tk.END, folder_path)  # Insert selected folder path
        
        # 清空当前列表
        listbox.delete(0, tk.END)
        
        # 扫描文件夹并更新列表
        parquet_files = [f for f in os.listdir(folder_path) if f.endswith('.parquet') and not f.startswith('.')]
        for file in parquet_files:
            listbox.insert(tk.END, file)


# Function to handle button click and open file dialog
def open_file_dialog(entry_widget, feature_parquet_entry):
    file_path = filedialog.askopenfilename(initialdir=feature_parquet_entry.get(), title="Select Parquet File", filetypes=(("Parquet files", "*.parquet"), ("All files", "*.*")))
    if file_path:
        entry_widget.delete(0, tk.END)  # Clear current content
        entry_widget.insert(0, file_path)  # Insert selected file path

import pygame

# Initialize the pygame mixer
pygame.mixer.init()


full_height = 750
image_width = 640
image_height = 360
default_father_folder = os.path.join( os.getcwd(), "./../Speaker")

class VideoAnnotationTool(tk.Tk):
    def __init__(self ):
        super().__init__()

        self.title("Video Annotation Tool")
        self.geometry(f"1200x{full_height+100}")

        # Setup the paned window
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel for the table
        self.left_panel = ttk.Frame(self.paned_window, width=600, height=full_height)
        self.table = ttk.Treeview(self.left_panel, columns=('一选(ctr+1)', '聚类(ctr+2)', '人物', '人物台词', 'Row Index'), show = "headings")
        for col in self.table['columns']:
            self.table.heading(col, text=col)
            self.table.column(col, width=120)
        self.table.pack(expand=True, fill=tk.BOTH)
        self.paned_window.add(self.left_panel)

        # Right panel for media display
        self.right_panel = ttk.Frame(self.paned_window, width=image_width, height=full_height)
        self.paned_window.add(self.right_panel)

        # Create a canvas for displaying the image
        self.image_canvas = tk.Canvas(self.right_panel, width=image_width, height=image_height, bg='white')
        self.image_canvas.pack(side=tk.TOP, padx=10, pady=10)

        self.audio_name = None
        # Create a play button
        # self.play_button = tk.Button(self, text="Play Sound", state=tk.DISABLED, command=self.play_sound_async)
        self.play_button = tk.Button(self.right_panel, text="Play Sound (ctrl+P) ", state=tk.DISABLED, command=self.play_sound)
        self.play_button.pack(side=tk.TOP, pady=10)

        # Separator before Image-Audio Data Directory
        self.separator1 = ttk.Separator(self.right_panel, orient=tk.HORIZONTAL)
        self.separator1.pack(fill=tk.X, padx=10, pady=5)

        # Button and Entry for Image-Audio Data Directory
        self.image_audio_frame = ttk.Frame(self.right_panel)
        self.image_audio_frame.pack(side=tk.TOP, pady=5)
        self.image_audio_entry = ttk.Entry(self.image_audio_frame, width=50)
        self.image_audio_entry.insert(tk.END, default_father_folder )
        self.image_audio_entry.pack(side=tk.LEFT)
        self.image_audio_button = ttk.Button(self.image_audio_frame, text="指定音频-图片父亲目录", command=lambda: open_directory_dialog(self.image_audio_entry))
        self.image_audio_button.pack(side=tk.LEFT)

        # Button and Entry for Feature-Parquet Directory
        self.feature_parquet_frame = ttk.Frame(self.right_panel)
        self.feature_parquet_frame.pack(side=tk.TOP, pady=5)
        self.feature_parquet_entry = ttk.Entry(self.feature_parquet_frame, width=50)
        self.feature_parquet_entry.insert(tk.END, self.image_audio_entry.get() )
        self.feature_parquet_entry.pack(side=tk.LEFT)
        # self.feature_parquet_button = ttk.Button(self.feature_parquet_frame, text="指定parquets文件目录", command=lambda: open_directory_dialog(self.feature_parquet_entry, self.image_audio_entry))
        self.feature_parquet_button = ttk.Button(self.feature_parquet_frame, text="指定parquets文件目录", command=lambda: open_directory_dialog_and_scan(self.feature_parquet_entry, self.feature_parquet_listbox, self.image_audio_entry))

        self.feature_parquet_button.pack(side=tk.LEFT)

        # Button and Entry for Pending Parquet Directory
        self.pending_parquet_frame = ttk.Frame(self.right_panel)
        self.pending_parquet_frame.pack(side=tk.TOP, pady=5)
        self.pending_parquet_entry = ttk.Entry(self.pending_parquet_frame, width=50)
        self.pending_parquet_entry.pack(side=tk.LEFT)
        self.pending_parquet_button = ttk.Button(self.pending_parquet_frame, text="指定待标注parquet文件", command=lambda: open_file_dialog(self.pending_parquet_entry, self.image_audio_entry))
        self.pending_parquet_button.pack(side=tk.LEFT)


        # Frame for Parquet file lists and buttons
        self.parquet_frame = ttk.Frame(self.right_panel)
        self.parquet_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=10, pady=10)

        # Listbox for Feature Parquet files
        self.feature_parquet_listbox = tk.Listbox(self.parquet_frame, selectmode=tk.SINGLE)
        self.feature_parquet_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Listbox for Previous Parquet files
        self.previous_parquet_listbox = tk.Listbox(self.parquet_frame, selectmode=tk.SINGLE)
        self.previous_parquet_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Middle frame for plus and minus buttons
        self.middle_frame = ttk.Frame(self.parquet_frame)
        self.middle_frame.pack(side=tk.TOP, pady=5)

        # Plus and minus buttons
        self.plus_button = ttk.Button(self.middle_frame, text="+", command=self.add_to_previous)
        self.plus_button.pack(side=tk.TOP, pady=5)
        self.minus_button = ttk.Button(self.middle_frame, text="-", command=self.remove_from_previous)
        self.minus_button.pack(side=tk.TOP, pady=5)

        # Frame for the bottom buttons
        self.bottom_frame = ttk.Frame(self.right_panel)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Save Annotation button
        self.save_button = ttk.Button(self.bottom_frame, text="保存标注", command=self.save_annotation)
        self.save_button.pack(side=tk.LEFT, pady=5)

        # Reload Data button
        self.reload_button = ttk.Button(self.bottom_frame, text="重新载入", command=self.reload_data)
        self.reload_button.pack(side=tk.RIGHT, pady=5)

        # Menu bar setup
        self.menu_bar = Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open")
        file_menu.add_command(label="Save")
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Status bar setup
        self.status_bar = ttk.Label(self, text="Hello World", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.video_data = None
        

        self.table.bind("<ButtonRelease-1>", self.on_cell_select)
        self.bind_all("<Control-c>", self.copy)
        self.bind_all("<Control-v>", self.paste)
        # bind ctrl+1 to apply_from_column
        self.bind_all("<Control-Key-1>",self.apply_from_column_0)
        self.bind_all("<Control-Key-2>",self.apply_from_column_1)
        self.copied_value = None

        # bind ctrl + P to play_sound
        self.bind_all("<Control-p>", self.play_sound)

        self.table.bind('<Double-1>', self.on_double_click)
        self.table.bind('<Button-3>', self.on_right_click)  # Bind right-click

    def save_temp(self):
        # 检查temp文件夹是否存在
        temp_folder = "temp"
        if not os.path.exists(temp_folder):
            # 如果不存在，则创建temp文件夹
            os.makedirs(temp_folder)

        # 获取pending_parquet_entry中的文件名
        pending_parquet_file = self.pending_parquet_entry.get()
        if pending_parquet_file.endswith('.parquet'):
            # 替换.parquet为_temp.parquet
            temp_parquet_file = pending_parquet_file[:-8] + '_temp.parquet'
        else:
            temp_parquet_file = pending_parquet_file + '_temp.parquet'

        # 保存到temp文件夹中
        temp_parquet_path = os.path.join(temp_folder, temp_parquet_file)
        self.video_data.save_parquets(temp_parquet_path)

    def save_annotation(self):

        initial_fname = self.pending_parquet_entry.get()
        if initial_fname.endswith('.parquet'):
            initial_fname = initial_fname[:-8] + '_label.parquet'


        # 创建一个对话框来让用户指定保存标注文件的目录
        save_path = filedialog.asksaveasfilename(initialdir=self.feature_parquet_entry.get(), defaultextension=".parquet", title="Save Annotation", initialfile= initial_fname)
        if not save_path:
            return

        # # 将pending_parquet_entry中的文件名转换为包含标注的文件名
        # pending_parquet_file = self.pending_parquet_entry.get()
        # if pending_parquet_file.endswith('.parquet'):
        #     labeled_parquet_file = pending_parquet_file[:-8] + '_label.parquet'
        # else:
        #     labeled_parquet_file = pending_parquet_file + '_label.parquet'

        # labeled_parquet_file = os.path.join(save_path, labeled_parquet_file)
        # 调用VideoData的相应方法来保存标注
        self.video_data.save_parquets( save_path )

    def reload_data(self):
        # 检查pending_parquet_entry的文件是否存在
        pending_parquet_file = self.pending_parquet_entry.get()
        if not os.path.exists(pending_parquet_file):
            # messagebox.showinfo("提示", "待标注的parquet文件不存在。")
            return
        
        # 检查image_audio_entry的文件夹是否存在
        image_audio_folder = self.image_audio_entry.get()
        if not os.path.exists(image_audio_folder):
            # messagebox.showinfo("提示", "音频-图片父亲目录不存在。")
            return
        
        parquet_folder = self.feature_parquet_entry.get()
        
        # 读取previous_parquet_listbox中的项目
        previous_parquet_files = [self.previous_parquet_listbox.get(i) for i in range(self.previous_parquet_listbox.size())]
        previous_parquet_files = [os.path.join(parquet_folder, file) for file in previous_parquet_files]

        # 使用这些变量来初始化一个新的VideoData实例
        video_data = VideoData(pending_parquet_file, image_audio_folder, previous_parquet_files)

        # 使用self.set_video_data进行更新
        self.set_video_data(video_data)

    def add_to_previous(self):
        # 获取feature_parquet_listbox中被选中的项目
        selected_items = self.feature_parquet_listbox.curselection()
        if not selected_items:
            # messagebox.showinfo("提示", "请选择要添加的项目。")
            return
        
        # 将选中的项目添加到previous_parquet_listbox
        for item in selected_items:
            self.previous_parquet_listbox.insert(tk.END, self.feature_parquet_listbox.get(item))
            # 从feature_parquet_listbox中移除该项目
            self.feature_parquet_listbox.delete(item)

    def remove_from_previous(self):
        # 获取previous_parquet_listbox中被选中的项目
        selected_items = self.previous_parquet_listbox.curselection()
        if not selected_items:
            # messagebox.showinfo("提示", "请选择要移除的项目。")
            return
        
        # 从previous_parquet_listbox中移除选中的项目
        for item in selected_items:
            self.feature_parquet_listbox.insert(tk.END, self.previous_parquet_listbox.get(item))
            self.previous_parquet_listbox.delete(item)
            

    def set_video_data( self, video_data ):

        self.video_data = video_data

        # Load data into the table
        self.load_data()

    # Method to play the audio file
    def play_sound(self, event = None):
        if self.audio_name:
            print("try play audio ", self.audio_name)
            playsound(self.audio_name)
            # current_dir = os.getcwd()
            # abs_path = os.path.join(current_dir, self.audio_name)
            # print(abs_path)
            # pygame.mixer.music.load(abs_path)
            # pygame.mixer.music.play()

    # Method to update the image display
    def update_image(self, index):
        image_fname = self.video_data.get_image_fname(index)
        if os.path.exists(image_fname):
            # Load the image and display it on the canvas
            image = Image.open(image_fname)
            image = image.resize((image_width, image_height), Image.ANTIALIAS)  # Resize the image to fit the canvas
            self.image = ImageTk.PhotoImage(image)
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.image)
        else:
            print("unfound image file:", image_fname)
            # Display a placeholder or empty image
            self.image_canvas.delete('all')

        # Check if the audio file exists
        audio_fname = self.video_data.get_audio_fname(index)

        audio_fname = audio_fname.replace("\\", "/")

        if os.path.exists(audio_fname):
            # Activate the play button
            self.play_button.config(state=tk.NORMAL, command=lambda: self.play_sound(index))
            self.audio_name = audio_fname
        else:
            # Disable the play button if the audio file does not exist
            self.play_button.config(state=tk.DISABLED)
            self.audio_name = None

    def apply_from_column_0(self, event):
        self.apply_from_column(event, 0)

    def apply_from_column_1(self, event):
        self.apply_from_column(event, 1)

    # 我希望增加一个方法 apply_from_column ，对于focus的行，检查第0列中的元素在extract_speaker_name函数中是否返回None
    # 如果不是None，则将该元素赋值给第3列
    def apply_from_column(self, event, column_index):
        self.status_bar.config(text="Applying from column...")
        row_id = self.table.focus()
        if row_id:
            content = self.table.set(row_id, column_index)
            speaker = extract_speaker_name(content)
            if speaker:
                self.set_new_value(row_id, 3, speaker)
            else:
                self.status_bar.config(text="Failed to apply from column")

    def move_focus_to_next_row(self, current_index ):
        # find next row
        children = self.table.get_children()
        # current_index = list(children).index(current_row_id)
        # current_index = self.get_row_index(current_row_id)
        next_index = current_index + 1

        if next_index < len(children):
            next_row_id = children[next_index]
            self.table.focus(next_row_id)
            self.table.selection_set(next_row_id)
            # Update the image display
            self.update_image(next_index)
        else:
            self.status_bar.config(text="End of file")

        
        

    def on_cell_select(self, event):
        row_id = self.table.focus()
        column = self.table.identify_column(event.x)
        self.status_bar.config(text=f"Selected Row: {row_id}")
        index = self.get_row_index(row_id)
        self.update_image(index)

        # col_index = self.table['columns'].index(column[1:]) + 1
        # self.status_bar.config(text=f"Selected Row: {row_id}, Column: {col_index}")
        # Additional code to highlight or bold can be added here.

    def copy(self, event):
        row_id = self.table.focus()
        column = self.table.identify_column(event.x)
        if row_id and column:
            content = self.table.set(row_id, column)
            if column != "#3":  # '人物' column
                speaker = extract_speaker_name(content)
            else:
                speaker = content
            if speaker:
                self.copied_value = speaker
                self.status_bar.config(text=f"Copied: {self.copied_value}")
                # 同时把speaker的信息存入剪贴板
                pyperclip.copy(speaker)
            else:
                self.status_bar.config(text=f"未能复制")

    def get_row_index(self, row_id):
        """Get the integer index for the given row_id."""
        children = self.table.get_children()
        try:
            index = list(children).index(row_id)
            return index
        except ValueError:
            return 0  # Or handle the error as needed
        
    def set_new_value( self, row_id, column,  new_value ):
        self.table.set(row_id, column, new_value)
        row_index = self.get_row_index(row_id)

        self.video_data.label_row( row_index, new_value )
        self.load_data()
        self.save_temp()

        self.move_focus_to_next_row(row_index)


    def paste(self, event):
        row_id = self.table.focus()
        column = self.table.identify_column(event.x)
        if row_id and column and self.copied_value and column == "#3":  # '人物' column
            self.table.set(row_id, column, self.copied_value)
            self.status_bar.config(text=f"Pasted: {self.copied_value} into Row: {row_id}, Column: {column}")            

            row_index = self.get_row_index(row_id)

            self.video_data.label_row( row_index, self.copied_value )
            self.load_data()
            self.save_temp()

            self.move_focus_to_next_row(row_index)

    def on_double_click(self, event):
        region = self.table.identify("region", event.x, event.y)
        if region == "cell":
            column = self.table.identify_column(event.x)
            if column == "#3":  # '人物' column
                row_id = self.table.identify_row(event.y)
                item = self.table.item(row_id)
                value = item['values'][2]  # Adjust index for '人物' column
                new_value = simpledialog.askstring("Update Info", "Edit the name:", initialvalue=value)
                if new_value:
                    self.set_new_value(row_id, column, new_value)
                    # self.table.set(row_id, column=column, value=new_value)

                    # row_index = self.get_row_index(row_id)

                    # self.video_data.label_row( row_index, new_value )
                    # self.load_data()

                    # self.move_focus_to_next_row(row_index)

    def on_right_click(self, event):
        iid = self.table.identify_row(event.y)
        if iid:
            # Set focus and selection on the right-clicked row
            self.table.focus(iid)
            self.table.selection_set(iid)
            item = self.table.item(iid)
            column = self.table.identify_column(event.x)
            self.clipboard_clear()
            self.clipboard_append(item['values'][self.table['columns'].index(column[1:])])  # Adjust index to get correct value
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Copy", command=lambda: self.clipboard_append(item['values'][self.table['columns'].index(column[1:])]))
            menu.tk_popup(event.x_root, event.y_root)

    def load_data(self):
        data = self.video_data.get_current_table()

        # Remove existing data
        for item in self.table.get_children():
            self.table.delete(item)
        # Insert new data
        for index, row in data.iterrows():
            self.table.insert('', 'end', values=(row['knn_result'], row['estimated_speaker'], row['人物'], row['人物台词'], index))

if __name__ == "__main__":

    inference_table = "./../Speaker/亮剑20_rm_name.parquet"

    previous_tables = [ "./../Speaker/亮剑12.parquet", "./../Speaker/亮剑13.parquet", "./../Speaker/亮剑15.parquet" ]

    data_folder = ".\..\Speaker"

    video_data = VideoData(inference_table, data_folder, previous_tables)

    video_data.compute_speaker()

    current_table = video_data.get_current_table()

    app = VideoAnnotationTool()
    app.set_video_data(video_data)
    app.mainloop()
