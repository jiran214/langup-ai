from langup import config, VideoCommentUP, DEFAULT


config.log['handlers'] = ['file', 'console']
config.proxy = 'http://127.0.0.1:7890'

up = VideoCommentUP(
    up_sleep=10,  # 生成回复间隔事件
    listener_sleep=60 * 2,  # 2分钟获取一次@消息
    system=DEFAULT,
    signals=['总结一下']
    # 建议将openai_api_key、credential写到 工作目录/.env文件，会自动读取
    # credential={"sessdata": 'xxx', "buvid3": 'xxx', "bili_jct": 'xxx'}
).loop()