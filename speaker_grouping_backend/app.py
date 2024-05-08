from websocketclient import create_connection

import json
import configparser

from VideoData import VideoData
import os

def get_parquets():
    import os
    parquets = []
    for file in os.listdir("content"):
        if file.endswith(".parquet"):
            parquets.append("content/" + file)
    return parquets

ws = create_connection()
config = configparser.ConfigParser()
config.read('config.ini')

# Send a message to the server
ws.send(
    json.dumps(
        {
            "type": "init",
            "data": {
                "username": config['DEFAULT']['Username'],
                "parquets": get_parquets()
            }
        }
    )
)

video_data = None

while True:
    # Receive a message from the server
    try:
        message = ws.recv()
    except:
        ws = create_connection()
        if ws == None:
            continue
        ws.send(
            json.dumps(
                {
                    "type": "init",
                    "data": {
                        "username": config['DEFAULT']['Username'],
                        "parquets": get_parquets()
                    }
                }
            )
        )
        continue
    print("Received message:", message)
    # Do something with the message

    data = json.loads(message)

    match data['type']:
        case 'load_dataset':
            # Do something with the grouping message

            inference_table_path = data['path']
            previous_tables_paths = data['previous_dataset']
            
            if inference_table_path == None:
                ws.send(json.dumps({"type": "load_dataset", "data": []}))
                continue



            video_data = VideoData(inference_table_path, None, previous_tables_paths)
            # print(video_data.previous_data.info())

            video_data.compute_speaker()

            # print(video_data.candidate_edges_on_self[5])
            # print(video_data.candidate_edges_on_previous[5])

            # print(video_data.sorted_edges[:15])


            vis_table = video_data.get_current_table()


            # vis_table转为json列表
            vis_table_json = vis_table.to_dict(orient='records')

            # 每一行加入图片和音频路径
            current_working_dir = os.getcwd() + "/source/"
            for i in range(len(vis_table_json)):
                vis_table_json[i]['image'] = "source/"+ video_data.get_image_fname(i)
                vis_table_json[i]['audio'] = "source/"+  video_data.get_audio_fname(i)
            print(vis_table_json)

            ws.send(json.dumps({"type": "load_dataset", "data": vis_table_json}))
            pass
        case 'modify_dataset':
            
            modfiy_datas = data['data']
            for modify_data in modfiy_datas:
                if modify_data["人物"] == None:
                    ws.send(json.dumps({"type": "modify_dataset", "data": []}))
                    break
                video_data.label_row(int(modify_data['id']), modify_data['人物'])
            else:
                vis_table = video_data.get_current_table()
                

                # vis_table转为json列表
                vis_table_json = vis_table.to_dict(orient='records')

                ws.send(json.dumps({"type": "load_dataset", "data": vis_table_json}))
                
            pass
            # Do something with other messages
        case 'save_dataset':
            vis_table = video_data.get_current_table()
            os.mkdir(f"Anno_result")
            filename = os.path.basename(inference_table_path)
            vis_table.to_csv(f"Anno_result/{filename}.csv", index=False)  
            pass
        case _:
            pass
            # Handle unknown message types