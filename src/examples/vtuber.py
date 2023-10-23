from langup import VtuBer, config

config.proxy = 'http://127.0.0.1:7890'
VtuBer(
    system="""角色：你现在是一位在哔哩哔哩网站的主播，你很熟悉哔哩哔哩上的网友发言习惯和平台调性，擅长与年轻人打交道。
背景：通过直播中和用户弹幕的互动，产出有趣的对话，以此吸引更多人来观看直播并关注你。
任务：你在直播过程中会对每一位直播间用户发的弹幕进行回答，但是要以“杠精”的思维去回答，你会怒怼这些弹幕，不放过每一条弹幕，每次回答字数不能超过100字。""",
    concurrent_num=1,
    room_id=5520,
    # 登录Bilibili 从浏览器获取cookie:https://nemo2011.github.io/bilibili-api/#/get-credential
    # 建议将openai_api_key、credential写到 工作目录/.env文件，会自动读取
    # credential={"sessdata": 'xxx', "buvid3": 'xxx', "bili_jct": 'xxx'}

).loop()
