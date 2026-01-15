---
name: video-filler-word-remover
description: 分析视频字幕文件，自动识别语气词（如"嗯"、"啊"、"那个"等），使用 ffmpeg 裁剪掉对应时间段，生成去除语气词的视频。适用于视频剪辑、内容优化场景。
allowed-tools: Read, Write, Bash
---

# 视频语气词移除工具

自动检测字幕中的语气词并裁剪视频对应片段。

## 功能说明

本 Skill 能够：
1. 读取并解析字幕文件（支持 SRT、VTT 等格式）
2. 识别常见的中文和英文语气词
3. 生成 ffmpeg 裁剪命令
4. 自动执行视频片段裁剪和拼接
5. 输出去除语气词后的最终视频

## 使用场景

- 清理采访、演讲、教学视频中的语气词
- 优化视频内容质量
- 批量处理多个视频文件
- 提升视频观看体验

## 支持的语气词列表

### 中文语气词
- 嗯、啊、呃、额
- 那个、这个、就是
- 然后、所以、但是（作为语气词使用时）
- 其实、可能、大概
- 哎、哦、诶

### 英文语气词
- um, uh, er, ah
- like, you know, I mean
- so, well, actually
- basically, literally

## 工作流程

### 步骤 1: 准备文件
确保您有以下文件：
- 原始视频文件（如 `input.mp4`）
- 对应的字幕文件（如 `input.srt` 或 `input.vtt`）

### 步骤 2: 分析字幕
我会读取字幕文件，识别包含语气词的时间段：

```python
# 示例：解析 SRT 字幕
import re

def parse_srt(srt_content):
    # 解析字幕条目
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    return matches

def detect_filler_words(text):
    # 中文语气词
    cn_fillers = ['嗯', '啊', '呃', '额', '那个', '这个', '就是', '然后', '哎', '哦', '诶']
    # 英文语气词
    en_fillers = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 'so', 'well']
    
    text_lower = text.lower()
    for filler in cn_fillers + en_fillers:
        if filler in text_lower:
            return True
    return False
```

### 步骤 3: 生成裁剪列表
创建需要保留的视频片段时间列表（排除语气词片段）。

### 步骤 4: 使用 ffmpeg 处理视频

我会生成并执行类似以下的命令：

```bash
# 方法 1: 使用 select 过滤器（适合少量片段）
ffmpeg -i input.mp4 \
  -vf "select='between(t,0,5.2)+between(t,6.8,15.3)+between(t,16.1,30.5)', setpts=N/FRAME_RATE/TB" \
  -af "aselect='between(t,0,5.2)+between(t,6.8,15.3)+between(t,16.1,30.5)', asetpts=N/SR/TB" \
  output.mp4

# 方法 2: 分段裁剪后拼接（适合大量片段）
# 1. 裁剪各个片段
ffmpeg -i input.mp4 -ss 00:00:00 -to 00:00:05.2 -c copy segment1.mp4
ffmpeg -i input.mp4 -ss 00:00:06.8 -to 00:00:15.3 -c copy segment2.mp4
ffmpeg -i input.mp4 -ss 00:00:16.1 -to 00:00:30.5 -c copy segment3.mp4

# 2. 创建拼接列表文件
cat > concat_list.txt << EOF
file 'segment1.mp4'
file 'segment2.mp4'
file 'segment3.mp4'
EOF

# 3. 拼接所有片段
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4
```

### 步骤 5: 生成新字幕
同步更新字幕文件，调整时间戳以匹配新视频。

## 依赖要求

需要在系统中安装 ffmpeg：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg
```

## 使用示例

### 基础用法
```
请帮我处理 interview.mp4 视频，移除字幕文件 interview.srt 中的所有语气词
```

### 高级用法
```
分析 lecture.mp4 和 lecture.vtt，识别中文语气词并生成去除后的视频，
同时保留原始文件，新视频命名为 lecture_clean.mp4
```

### 批量处理
```
处理 videos 目录下所有 mp4 文件，每个视频都有对应的 srt 字幕，
移除语气词并保存到 output 目录
```

## 配置选项

可以自定义的参数：
- **语气词列表**：添加或删除特定的语气词
- **时间缓冲**：在语气词前后添加额外的裁剪时间（如 0.2 秒）
- **最小片段长度**：忽略过短的语气词片段（如小于 0.5 秒）
- **输出质量**：选择 `-c copy`（快速）或重新编码（质量优化）

## 注意事项

1. **备份原文件**：处理前请备份原始视频和字幕
2. **检查结果**：建议先处理一小段测试效果
3. **性能考虑**：大文件处理可能需要较长时间
4. **格式兼容**：确保视频和字幕格式匹配
5. **语气词误判**：某些正常词汇可能被误判，建议人工审核

## 故障排查

### ffmpeg 未安装
如果提示找不到 ffmpeg，请先安装：
```bash
which ffmpeg  # 检查是否已安装
```

### 字幕格式不支持
目前支持 SRT 和 VTT 格式。如需其他格式，可以使用在线工具转换。

### 视频音频不同步
如果出现同步问题，尝试使用 `-async 1` 参数重新编码。

### 输出文件过大
使用编码参数优化：
```bash
ffmpeg -i input.mp4 ... -c:v libx264 -crf 23 -c:a aac output.mp4
```

## 最佳实践

1. **先分析后执行**：让我先展示将要裁剪的片段列表，确认后再执行
2. **分步处理**：对于长视频，可以分段处理避免一次性失败
3. **保留日志**：记录裁剪的时间段，便于后续审查
4. **质量检查**：处理后播放检查是否有遗漏或错误裁剪

## 输出文件

处理完成后会生成：
- `{原文件名}_no_fillers.mp4` - 去除语气词的视频
- `{原文件名}_no_fillers.srt` - 更新后的字幕文件
- `removed_segments.json` - 被移除片段的详细记录
- `processing_log.txt` - 处理日志

## 进阶功能

### 自定义语气词检测
可以使用正则表达式或 AI 模型进行更智能的检测：
- 基于上下文判断是否为语气词
- 识别重复词汇
- 检测停顿和沉默片段

### 批量优化
对多个视频应用相同的处理规则，提高效率。