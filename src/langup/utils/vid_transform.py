Str = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'  # 准备的一串指定字符串
Dict = {}  # 建立一个空字典

# 将字符串的每一个字符放入字典一一对应 ， 如 f对应0 Z对应1 一次类推。
for i in range(58):
    Dict[Str[i]] = i
# print(tr) #如果你实在不理解请将前面的注释去掉，查看字典的构成

s = [11, 10, 3, 8, 4, 6, 2, 9, 5, 7]  # 必要的解密列表
xor = 177451812  # 必要的解密数字 通过知乎大佬的观察计算得出 网址：https://www.zhihu.com/question/381784377
add = 100618342136696320  # 这串数字最后要被减去或加上


# 解密BV号
def bv2aid(bv):
    if bv.find('BV') == -1:
        bv = 'BV' + bv

    r = 0
    # 下面的代码是将BV号的编码对照字典转化并进行相乘相加操作 **为乘方
    for i in range(10):
        r += Dict[bv[s[i]]] * 58 ** i

    # 将结果与add相减并进行异或计算
    return str((r - add) ^ xor)


# 加密AV号
def aid2bv(av):
    ret = av
    av = int(av)
    # 将AV号传入结果进行异或计算并加上 100618342136696320
    av = (av ^ xor) + add
    # 将BV号的格式（BV + 10个字符） 转化成列表方便后面的操作
    r = list('BV          ')
    # 将传入的数字对照字典进行转化
    for i in range(10):
        r[s[i]] = Str[av // 58 ** i % 58]
    # 将转化好的列表数据重新整合成字符串
    return ''.join(r)


def note_query_2_aid(note_query: str):
    if note_query.startswith('BV'):
        aid = bv2aid(note_query)
    elif note_query.startswith('https://www.bilibili.com/video/BV'):
        bv = note_query.split('https://www.bilibili.com/video/')[1].split('/')[0]
        aid = bv2aid(bv)
    else:
        aid = note_query

    return int(aid)