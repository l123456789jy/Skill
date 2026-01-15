#!/usr/bin/env python3
"""
语气词检测和视频处理脚本
分析字幕文件，检测语气词并生成 ffmpeg 裁剪命令
"""

import re
import json
import argparse
from datetime import timedelta
from typing import List, Tuple, Dict

# 语气词词典
FILLER_WORDS = {
    'zh': ['嗯', '啊', '呃', '额', '那个', '这个', '就是', '然后', '哎', '哦', '诶', 
           '其实', '可能', '大概', '嗯嗯', '啊啊'],
    'en': ['um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 'so', 'well', 
           'actually', 'basically', 'literally', 'kind of', 'sort of']
}

def parse_time(time_str: str) -> float:
    """将 SRT 时间格式转换为秒"""
    # 支持格式: 00:00:05,200 或 00:00:05.200
    time_str = time_str.replace(',', '.')
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def format_time(seconds: float) -> str:
    """将秒转换为 SRT 时间格式"""
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def parse_srt(file_path: str) -> List[Dict]:
    """解析 SRT 字幕文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配字幕条目
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})\n(.*?)(?=\n\n|\n\d+\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    subtitles = []
    for match in matches:
        index, start, end, text = match
        subtitles.append({
            'index': int(index),
            'start': parse_time(start),
            'end': parse_time(end),
            'text': text.strip()
        })
    
    return subtitles

def detect_filler_in_text(text: str, language: str = 'both') -> bool:
    """检测文本中是否包含语气词"""
    text_lower = text.lower()
    
    # 移除标点符号进行检测
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    
    if language in ['zh', 'both']:
        for filler in FILLER_WORDS['zh']:
            if filler in text:
                return True
    
    if language in ['en', 'both']:
        for filler in FILLER_WORDS['en']:
            # 使用单词边界匹配，避免误判
            if re.search(r'\b' + re.escape(filler) + r'\b', text_clean):
                return True
    
    return False

def get_keep_segments(subtitles: List[Dict], buffer_seconds: float = 0.1) -> List[Tuple[float, float]]:
    """
    获取需要保留的视频片段（排除语气词片段）
    buffer_seconds: 在语气词前后添加的缓冲时间
    """
    keep_segments = []
    current_start = 0.0
    
    for sub in subtitles:
        if detect_filler_in_text(sub['text']):
            # 发现语气词，保存之前的片段
            segment_end = max(0, sub['start'] - buffer_seconds)
            if current_start < segment_end:
                keep_segments.append((current_start, segment_end))
            # 下一段从语气词结束后开始
            current_start = sub['end'] + buffer_seconds
    
    # 添加最后一段（从最后一个语气词到视频结尾）
    # 注意：这里需要知道视频总长度，暂时使用最后一个字幕的结束时间
    if subtitles:
        video_end = subtitles[-1]['end'] + 10  # 假设字幕后还有10秒
        if current_start < video_end:
            keep_segments.append((current_start, video_end))
    
    return keep_segments

def merge_close_segments(segments: List[Tuple[float, float]], min_gap: float = 1.0) -> List[Tuple[float, float]]:
    """合并间隔很小的片段，避免过度碎片化"""
    if not segments:
        return []
    
    merged = [segments[0]]
    
    for current_start, current_end in segments[1:]:
        last_start, last_end = merged[-1]
        
        if current_start - last_end < min_gap:
            # 合并片段
            merged[-1] = (last_start, current_end)
        else:
            merged.append((current_start, current_end))
    
    return merged

def generate_ffmpeg_command(input_video: str, segments: List[Tuple[float, float]], 
                           output_video: str, method: str = 'concat') -> str:
    """
    生成 ffmpeg 命令
    method: 'select' 或 'concat'
    """
    if method == 'select':
        # 方法 1: 使用 select 滤镜（适合少量片段）
        select_expr = '+'.join([f"between(t,{s},{e})" for s, e in segments])
        cmd = f"""ffmpeg -i "{input_video}" \\
  -vf "select='{select_expr}',setpts=N/FRAME_RATE/TB" \\
  -af "aselect='{select_expr}',asetpts=N/SR/TB" \\
  "{output_video}" """
        
    else:  # concat
        # 方法 2: 分段裁剪后拼接（更稳定）
        cmd_parts = []
        
        # 生成裁剪命令
        for i, (start, end) in enumerate(segments):
            segment_file = f"segment_{i:03d}.mp4"
            cmd_parts.append(f'ffmpeg -i "{input_video}" -ss {start} -to {end} -c copy {segment_file}')
        
        # 生成拼接列表
        cmd_parts.append("cat > concat_list.txt << EOF")
        for i in range(len(segments)):
            cmd_parts.append(f"file 'segment_{i:03d}.mp4'")
        cmd_parts.append("EOF")
        
        # 拼接命令
        cmd_parts.append(f'ffmpeg -f concat -safe 0 -i concat_list.txt -c copy "{output_video}"')
        
        # 清理临时文件
        cmd_parts.append("rm segment_*.mp4 concat_list.txt")
        
        cmd = '\n'.join(cmd_parts)
    
    return cmd

def generate_processing_script(input_video: str, subtitle_file: str, 
                               output_video: str = None) -> Dict:
    """生成完整的处理脚本和信息"""
    if output_video is None:
        base_name = input_video.rsplit('.', 1)[0]
        output_video = f"{base_name}_no_fillers.mp4"
    
    # 解析字幕
    subtitles = parse_srt(subtitle_file)
    
    # 获取需要保留的片段
    keep_segments = get_keep_segments(subtitles)
    
    # 合并间隔很小的片段
    keep_segments = merge_close_segments(keep_segments, min_gap=1.0)
    
    # 计算统计信息
    total_removed = sum([sub['end'] - sub['start'] 
                        for sub in subtitles 
                        if detect_filler_in_text(sub['text'])])
    
    original_duration = subtitles[-1]['end'] if subtitles else 0
    final_duration = sum([end - start for start, end in keep_segments])
    
    # 生成 ffmpeg 命令
    ffmpeg_cmd = generate_ffmpeg_command(input_video, keep_segments, output_video, method='concat')
    
    # 识别的语气词片段
    filler_segments = [sub for sub in subtitles if detect_filler_in_text(sub['text'])]
    
    result = {
        'input_video': input_video,
        'subtitle_file': subtitle_file,
        'output_video': output_video,
        'statistics': {
            'original_duration': f"{original_duration:.2f}s",
            'final_duration': f"{final_duration:.2f}s",
            'removed_duration': f"{total_removed:.2f}s",
            'filler_count': len(filler_segments),
            'segments_kept': len(keep_segments)
        },
        'filler_segments': [
            {
                'index': seg['index'],
                'time': f"{format_time(seg['start'])} --> {format_time(seg['end'])}",
                'text': seg['text']
            }
            for seg in filler_segments
        ],
        'keep_segments': [
            {'start': f"{s:.2f}s", 'end': f"{e:.2f}s", 'duration': f"{e-s:.2f}s"}
            for s, e in keep_segments
        ],
        'ffmpeg_command': ffmpeg_cmd
    }
    
    return result

def main():
    parser = argparse.ArgumentParser(description='检测字幕中的语气词并生成视频处理命令')
    parser.add_argument('video', help='输入视频文件')
    parser.add_argument('subtitle', help='字幕文件 (.srt)')
    parser.add_argument('-o', '--output', help='输出视频文件名')
    parser.add_argument('--execute', action='store_true', help='直接执行 ffmpeg 命令')
    parser.add_argument('--json', help='保存结果到 JSON 文件')
    
    args = parser.parse_args()
    
    # 生成处理信息
    result = generate_processing_script(args.video, args.subtitle, args.output)
    
    # 打印统计信息
    print("\n=== 视频处理分析 ===")
    print(f"输入视频: {result['input_video']}")
    print(f"字幕文件: {result['subtitle_file']}")
    print(f"输出视频: {result['output_video']}")
    print(f"\n统计信息:")
    for key, value in result['statistics'].items():
        print(f"  {key}: {value}")
    
    print(f"\n检测到的语气词片段 ({len(result['filler_segments'])} 个):")
    for seg in result['filler_segments'][:5]:  # 只显示前5个
        print(f"  [{seg['time']}] {seg['text']}")
    if len(result['filler_segments']) > 5:
        print(f"  ... 还有 {len(result['filler_segments']) - 5} 个")
    
    print(f"\n生成的 ffmpeg 命令:")
    print(result['ffmpeg_command'])
    
    # 保存到 JSON
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.json}")
    
    # 执行命令
    if args.execute:
        import subprocess
        print("\n正在执行 ffmpeg 命令...")
        subprocess.run(result['ffmpeg_command'], shell=True)
        print("处理完成！")

if __name__ == '__main__':
    main()