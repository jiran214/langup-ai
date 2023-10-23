from langup import config, VideoCommentUP


config.log['handlers'] = ['file', 'console']
config.proxy = 'http://127.0.0.1:7890'

up = VideoCommentUP(
    up_sleep=10,  # 生成回复间隔事件
    listener_sleep=60 * 2,  # 2分钟获取一次@消息
    system="你是一个会评论视频B站用户，请根据视频内容做出总结、评论",
    signals=['总结一下']
    # 建议将openai_api_key、credential写到 工作目录/.env文件，会自动读取
    # credential={"sessdata": 'xxx', "buvid3": 'xxx', "bili_jct": 'xxx'}
).loop()