from websocketclient import create_connection

import json
import configparser

from VideoData import VideoData

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

while True:
    # Receive a message from the server
    message = ws.recv()
    print("Received message:", message)
    # Do something with the message

    data = json.loads(message)

    match data['type']:
        case 'load_dataset':
            # Do something with the grouping message

            inference_table_path = data['path']
            previous_tables_paths = data['previous_dataset']
            

            video_data = VideoData(inference_table_path, None, previous_tables_paths)
            # print(video_data.previous_data.info())

            video_data.compute_speaker()

            # print(video_data.candidate_edges_on_self[5])
            # print(video_data.candidate_edges_on_previous[5])

            # print(video_data.sorted_edges[:15])


            vis_table = video_data.get_current_table()
            # vis_table转为json列表
            # vis_table_json = vis_table.to_dict(orient='records')


            ws.send(json.dumps({"type": "load_dataset", "data": vis_table.to_dict(orient='records')}))
            pass
        case 'modify_dataset':

            pass
            # Do something with other messages
        case _:
            pass
            # Handle unknown message types