from langup import UserInputReplyUP, config, DEFAULT

# config.proxy = 'http://127.0.0.1:7890'
# config.openai_api_key = 'xxx' or 创建.env文件 OPENAI_API_KEY=xxx

# 1. 终端回复
# UserInputReplyUP(system=DEFAULT, listen='console').loop()

# 2. 语音实时识别回复
# config.convert['speech_rec']修改语音识别模块配置
# UserInputReplyUP(system=DEFAULT, listen='speech').loop()  # 语音识别回复
