# 初始化建立连接

## 请求
```json
{
    "type": "init",
    "data": {
        "username": "admin",
        "parquets": [
            "content/xx.parquet",
            "content/xx.parquet"
        ]
    }
}
```

# 加载指定数据集

## 请求
```json
{
    "type": "load_dataset",
    "path": "content/xx.parquet",
    "previous_dataset": [
        "content/xx.parquet",
        "content/xx.parquet"
    ]
}
```

## 响应
```json
{
    "type": "load_dataset",
    "data": [
        {
            "knn_result": "刑副团长_0.48",
            "estimated_speaker": 0,
            "人物": "赵刚",
            "人物台词": "咱谁也不怕",
            "开始时间": "00:01:34.620",
            "image": "content/xx.jpg",
            "audio": "content/xx.wav"
        },
        {
            "knn_result": "刑副团长_0.48",
            "estimated_speaker": 0,
            "人物": "赵刚",
            "人物台词": "咱谁也不怕",
            "开始时间": "00:01:34.620",
            "image": "content/xx.jpg",
            "audio": "content/xx.wav"
        }
    ]
}
```

# 修改指定数据集

服务器保存时请求调用

## 请求
```json
{
    "type": "modify_dataset",
    "data": [
        {
            "id": 0,
            "人物": "赵刚",
        }
    ]
}
```

## 响应
```json
{
    "type": "modify_dataset",
    "status": "success"
}
```