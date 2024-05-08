
# from srt2csv import convert
# import os
# pp = "D:/haruhivideo/[CASO][Suzumiya_Haruhi_no_Yuuutsu][BDRIP][Subtitle_SC][ASS]/"

# ff = os.listdir(pp)

# for f in ff:
#     convert(f"{pp}/{f}", "outsrtcsv", True)
# exit()

import pysubs2
import csv
import os
import pysrt

def convert_ass_to_csv(ass_file_path, csv_file_path):
    # 加载 ASS 文件
    subs = pysubs2.load(ass_file_path, encoding="utf-16le")
    
    # 创建或覆盖 CSV 文件，并写入字幕信息
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["人物", "人物台词", "开始时间", "结束时间"])  # 写入表头
        
        for line in subs:
            # 将字幕的开始时间、结束时间转换为时间字符串
            start_time = str(line.start)
            # 将秒转换为时间字符串
            def convert_seconds_to_time(seconds):
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                time_string = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                return time_string

            # 示例：将字幕的开始时间、结束时间转换为时间字符串
            start_time = convert_seconds_to_time(line.start)
            end_time = convert_seconds_to_time(line.end)
            # 将字幕的开始时间、结束时间和文本写入 CSV
            writer.writerow(["", line.text, start_time, end_time])

def convert_srt_to_csv(srt_file_path, csv_file_path):
    # 加载 SRT 文件
    subs = pysrt.open(srt_file_path, encoding="utf-8")
    
    # 创建或覆盖 CSV 文件，并写入字幕信息
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["人物", "人物台词", "开始时间", "结束时间"])  # 写入表头
        
        for line in subs:
            # 将字幕的开始时间、结束时间转换为时间字符串
            # 将字幕的开始时间、结束时间和文本写入 CSV
            start_time = str(line.start.to_time())
            end_time = str(line.end.to_time())

            writer.writerow(["", line.text, start_time, end_time])

def main():

    # ass_folder = "D:/haruhivideo/[CASO][Suzumiya_Haruhi_no_Yuuutsu][BDRIP][Subtitle_SC][ASS]/"
    ass_folder = "out"
    file_list = os.listdir(ass_folder)

    for f in file_list:
        if f.endswith(".ass"):  # 确保处理的是 ASS 文件
            try:
                ass_file_path = os.path.join(ass_folder, f)
                csv_file_path = os.path.join("outsrtcsv", f.replace(".ass", ".csv"))
                convert_ass_to_csv(ass_file_path, csv_file_path)
            except Exception as e:
                print(f"Error processing {f}: {e}")

        elif f.endswith(".srt"):
            try:
                ass_file_path = os.path.join(ass_folder, f)
                csv_file_path = os.path.join("outsrtcsv1", f.replace(".ass", ".csv"))
                convert_srt_to_csv(ass_file_path, csv_file_path)
            except Exception as e:
                print(f"Error processing {f}: {e}")
            

            
if __name__ == "__main__":
    main()