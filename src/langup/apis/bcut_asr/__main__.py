import logging
import sys
import time
from argparse import ArgumentParser, FileType
import ffmpeg
from . import APIError, BcutASR, ResultStateEnum

logging.basicConfig(format='%(asctime)s - [%(levelname)s] %(message)s', level=logging.INFO)

INFILE_FMT = ('flac', 'aac', 'm4a', 'mp3', 'wav')
OUTFILE_FMT = ('srt', 'json', 'lrc', 'txt')

parser = ArgumentParser(
    prog='bcut-asr',
    description='必剪语音识别\n',
    epilog=f"支持输入音频格式: {', '.join(INFILE_FMT)}  支持自动调用ffmpeg提取视频伴音"
)
parser.add_argument('-f', '--format', nargs='?', default='srt', choices=OUTFILE_FMT, help='输出字幕格式')
parser.add_argument('input', type=FileType('rb'), help='输入媒体文件')
parser.add_argument('output', nargs='?', type=FileType('w', encoding='utf8'), help='输出字幕文件, 可stdout')

args = parser.parse_args()


def ffmpeg_render(media_file: str) -> bytes:
    '提取视频伴音并转码为aac格式'
    out, err = (ffmpeg
                .input(media_file, v='warning')
                .output('pipe:', ac=1, format='adts')
                .run(capture_stdout=True)
                )
    return out


def main():
    # 处理输入文件情况
    infile = args.input
    infile_name = infile.name
    if infile_name == '<stdin>':
        logging.error('输入文件错误')
        sys.exit(-1)
    suffix = infile_name.rsplit('.', 1)[-1]
    if suffix in INFILE_FMT:
        infile_fmt = suffix
        infile_data = infile.read()
    else:
        # ffmpeg分离视频伴音
        logging.info('非标准音频文件, 尝试调用ffmpeg转码')
        try:
            infile_data = ffmpeg_render(infile_name)
        except ffmpeg.Error:
            logging.error('ffmpeg转码失败')
            sys.exit(-1)
        else:
            logging.info('ffmpeg转码完成')
            infile_fmt = 'aac'

    # 处理输出文件情况
    outfile = args.output
    if outfile is None:
        # 未指定输出文件，默认为文件名同输入，可以 -t 传参，默认str格式
        if args.format is not None:
            outfile_fmt = args.format
        else:
            outfile_fmt = 'srt'
        outfile_name = f"{infile_name.rsplit('.', 1)[-2]}.{outfile_fmt}"
        outfile = open(outfile_name, 'w', encoding='utf8')
    else:
        # 指定输出文件
        outfile_name = outfile.name
        if outfile.name == '<stdout>':
            # stdout情况，可以 -t 传参，默认str格式
            if args.format is not None:
                outfile_fmt = args.format
            else:
                outfile_fmt = 'srt'
        else:
            suffix = outfile_name.rsplit('.', 1)[-1]
            if suffix in OUTFILE_FMT:
                outfile_fmt = suffix
            else:
                logging.error('输出格式错误')
                sys.exit(-1)

    # 开始执行转换逻辑
    asr = BcutASR()
    asr.set_data(raw_data=infile_data, data_fmt=infile_fmt)
    try:
        # 上传文件
        asr.upload()
        # 创建任务
        task_id = asr.create_task()
        while True:
            # 轮询检查任务状态
            task_resp = asr.result()
            if task_resp.state == ResultStateEnum.STOP:
                logging.info(f'等待识别开始')
            if task_resp.state == ResultStateEnum.RUNING:
                logging.info(f'识别中-{task_resp.remark}')
            if task_resp.state == ResultStateEnum.ERROR:
                logging.error(f'识别失败-{task_resp.remark}')
                sys.exit(-1)
            if task_resp.state == ResultStateEnum.COMPLETE:
                logging.info(f'识别成功')
                # 识别成功, 回读字幕数据
                result = task_resp.parse()
                break
            time.sleep(1.0)
        if not result.has_data():
            logging.error('未识别到语音')
            sys.exit(-1)
        if outfile_fmt == 'srt':
            outfile.write(result.to_srt())
        if outfile_fmt == 'lrc':
            outfile.write(result.to_lrc())
        if outfile_fmt == 'json':
            outfile.write(result.json())
        if outfile_fmt == 'txt':
            outfile.write(result.to_txt())
        logging.info(f'转换成功: {outfile_name}')
    except APIError as err:
        logging.error(f'接口错误: {err.__str__()}')
        sys.exit(-1)


if __name__ == '__main__':
    main()
