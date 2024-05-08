# 我希望实现一个简单的字符串处理函数 输入形如 楚云飞_0.61 的字符串，输出 楚云飞
# 即判断 第一个_的位置，输出前面的字符串，
# 如果没有_， 则输出None

def extract_speaker_name(string):
    if '_' in string:
        return string[:string.index('_')]
    else:
        return None