## 读取csv文件 并将台词对应的音频切割出来 并截取一张关键帧

import pandas as pd

import argparse 
import ffmpeg

import os
import re
from datetime import datetime
import subprocess

# 设置 ffmpeg 日志级别为quiet
ffmpeg_loglevel = "quiet"

def trim_audio(input_file, output_file, start_time, end_time):
    output_file1 = output_file.replace(".wav", ".mp4")
    trim_video(input_file, output_file1, start_time, end_time)
    video_to_audio(output_file1, output_file)
    os.remove(output_file1)



def trim_video(input_file, output_file, start_time, end_time):
    # 构建 FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_file,         # 输入文件路径
        '-ss', str(start_time),  # 起始时间
        '-to', str(end_time),     # 截取时长
        '-c', 'copy',             # 使用相同编解码器进行复制
        '-avoid_negative_ts', '1', # 避免负时间戳
        '-loglevel', ffmpeg_loglevel,  # 日志级别
        '-y',                    # 覆盖输出文件
        output_file               # 输出文件路径
    ]
    print(ffmpeg_cmd)
    # 执行 FFmpeg 命令
    subprocess.run(ffmpeg_cmd)

def trim_video1(input_file, output_file, start_time, duration):
    # 构建 FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-ss', str(start_time),  # 起始时间
        '-i', input_file,         # 输入文件路径
        '-t', str(duration),     # 截取时长
        '-c', 'copy',             # 使用相同编解码器进行复制
        '-avoid_negative_ts', '1', # 避免负时间戳
        '-loglevel', ffmpeg_loglevel,  # 日志级别
        '-y',                    # 覆盖输出文件
        output_file               # 输出文件路径
    ]
    # 执行 FFmpeg 命令
    subprocess.run(ffmpeg_cmd)

def video_to_audio(input_file, output_file):
    # 构建 FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_file,         # 输入文件路径
        '-loglevel', ffmpeg_loglevel,  # 日志级别
        '-y',                    # 覆盖输出文件
        output_file               # 输出文件路径
    ]
    print(ffmpeg_cmd)
    # 执行 FFmpeg 命令
    subprocess.run(ffmpeg_cmd)

def get_screen_shot(input_file, output_file, time):
    # 构建 FFmpeg 命令
    ffmpeg_cmd = [
        'ffmpeg',
        '-ss', str(time),  # 截图时间
        '-i', input_file,         # 输入文件路径
        '-vframes', '1',     # 截取一帧
        '-q:v', '2',             # 图像质量
        '-loglevel', ffmpeg_loglevel,  # 日志级别
        '-y',                    # 覆盖输出文件
        output_file               # 输出文件路径
    ]

    # 执行 FFmpeg 命令
    subprocess.run(ffmpeg_cmd)

def make_filename_safe(filename):
    # 将非法字符替换为下划线
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    # 去除多余的空格
    filename = re.sub(r'\s+', ' ', filename)
    # 去除开头和结尾的空格
    filename = filename.strip()
    return filename


def get_audio(video_file, start_time, end_time, output_audio):
    stream = ffmpeg.input(video_file)
    stream = ffmpeg.output(stream, output_audio, ss=start_time, to=end_time)
    ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

def get_frame(video_file, time, output_frame):
    stream = ffmpeg.input(video_file)
    stream = ffmpeg.output(stream, output_frame, ss=time, vframes=1)
    ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)


def read_csv(csv_file):
    df = pd.read_csv(csv_file)
    return df

import PIL.Image as Image

# 将图片resize成480p
def resize_img(img_pth):
    img = Image.open(img_pth)
    img = img.resize((854, 480))
    img.save(img_pth)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_file', type=str, required=True)
    parser.add_argument('--input_video', type=str, required=True)
    parser.add_argument('--output_folder', type=str, required=False, default="outdata")
    args = parser.parse_args()
    df = read_csv(args.csv_file)
    # print(df.head())


    video_name =  make_filename_safe(os.path.basename(args.input_video))
    # 去除后缀
    video_name = os.path.splitext(video_name)[0]

    os.makedirs(f"{args.output_folder}/{video_name}", exist_ok=True)
    os.makedirs(f"{args.output_folder}/{video_name}/audios", exist_ok=True)
    os.makedirs(f"{args.output_folder}/{video_name}/screeshots", exist_ok=True)

    for index, row in df.iterrows():
        start_time = row['开始时间']
        end_time = row['结束时间']

        # start_time 转换为秒
        start_time_obj = datetime.strptime(start_time, "%H:%M:%S.%f")
        end_time_obj = datetime.strptime(end_time, "%H:%M:%S.%f")


        output_audio = f"{args.output_folder}/{video_name}/audios/{index}.wav"
        output_frame = f"{args.output_folder}/{video_name}/screeshots/{index}.jpg"
        # 求出中间时间
        middle_seconds = (end_time_obj - start_time_obj) / 2

        # 将偏移秒数加到开始时间的时间戳上，得到中间时间点的时间戳
        middle_time_obj = start_time_obj + middle_seconds
        # 将time转换为时分秒
        time = middle_time_obj.strftime("%H:%M:%S.%f")
        # time = start_time.strftime("%H:%M:%S.%f")
        # get_frame(args.input_video, time, output_frame)
        # get_audio(args.input_video, start_time, end_time, output_audio)
        # trim_video(args.input_video, f"{args.output_folder}/{video_name}/{index}.mp4", start_time, (end_time_obj - start_time_obj).seconds)
        # trim_audio(args.input_video, output_audio, start_time, end_time)
        trim_audio(args.input_video, output_audio, start_time, end_time)
        get_screen_shot(args.input_video, output_frame, time)
        # resize_img(output_frame)
        # 在本行中添加音频和截图的路径
        df.loc[index, 'audio_file'] = f"audios/{index}.wav"
        df.loc[index, 'screeshot_file'] = f"screeshots/{index}.jpg"

        print(f"clip {index} done")
    
    df.to_json(f"{args.output_folder}/{video_name}/meta.jsonl", orient='records', lines=True, force_ascii=False)

if __name__ == "__main__":
    main()