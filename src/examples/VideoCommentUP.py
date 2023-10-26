from langup import config, VideoCommentUP


config.log['handlers'] = ['file', 'console']
config.proxy = 'http://127.0.0.1:7890'

up = VideoCommentUP(
    up_sleep=10,  # 生成回复间隔事件
    listener_sleep=60 * 2,  # 2分钟获取一次@消息
    system="你是一个会评论视频B站用户，请根据视频内容做出总结、评论",
    signals=['总结一下'],
    # 方式一: credential为空，从工作目录/.env文件读取credential
    # 方式二: 直接传入
    # credential={"sessdata": 'xxx', "buvid3": 'xxx', "bili_jct": 'xxx'}
    # 方式三: 从浏览器资源读取
    # browser='edge'
).loop()