# 使用指南

## 快速开始

### 1. 安装 Skill

在您的项目根目录中创建 Skill：

```bash
mkdir -p .claude/skills/video-filler-word-remover
cd .claude/skills/video-filler-word-remover

# 复制以下文件：
# - SKILL.md
# - scripts/detect_fillers.py
# - USAGE.md
```

### 2. 安装依赖

确保系统已安装 ffmpeg：

```bash
# 检查是否已安装
ffmpeg -version

# macOS 安装
brew install ffmpeg

# Ubuntu/Debian 安装
sudo apt-get update
sudo apt-get install ffmpeg

# Windows 安装
# 从 https://ffmpeg.org/download.html 下载
# 或使用 Chocolatey: choco install ffmpeg
```

### 3. 准备文件

确保您有：
- 视频文件（如 `interview.mp4`）
- 对应的字幕文件（如 `interview.srt`）

字幕文件格式示例：
```
1
00:00:00,000 --> 00:00:02,500
大家好，今天我们来讨论一个话题

2
00:00:02,800 --> 00:00:04,200
嗯，这个话题很重要

3
00:00:04,500 --> 00:00:07,000
那个，我们先从基础开始
```

## 使用方式

### 方式 1: 通过 Claude Code 对话

直接与 Claude 对话，描述您的需求：

```
请帮我处理 interview.mp4 视频，它有对应的字幕文件 interview.srt，
移除所有语气词，生成新的视频文件
```

Claude 会自动：
1. 读取并分析字幕文件
2. 识别语气词片段
3. 生成 ffmpeg 处理命令
4. 询问是否执行
5. 执行并生成新视频

### 方式 2: 直接运行脚本

```bash
# 分析并显示结果（不执行）
python scripts/detect_fillers.py interview.mp4 interview.srt

# 分析并保存结果到 JSON
python scripts/detect_fillers.py interview.mp4 interview.srt --json result.json

# 直接执行处理
python scripts/detect_fillers.py interview.mp4 interview.srt --execute

# 指定输出文件名
python scripts/detect_fillers.py interview.mp4 interview.srt -o clean_interview.mp4 --execute
```

## 高级功能

### 自定义语气词列表

编辑 `scripts/detect_fillers.py` 中的 `FILLER_WORDS` 字典：

```python
FILLER_WORDS = {
    'zh': ['嗯', '啊', '呃', '额', '那个', '这个', '自定义语气词'],
    'en': ['um', 'uh', 'er', 'custom_filler']
}
```

### 调整时间缓冲

在 `get_keep_segments` 函数中修改 `buffer_seconds` 参数：

```python
# 在语气词前后各留 0.2 秒缓冲
keep_segments = get_keep_segments(subtitles, buffer_seconds=0.2)
```

### 批量处理多个视频

```bash
# 创建批处理脚本
for video in *.mp4; do
    subtitle="${video%.mp4}.srt"
    if [ -f "$subtitle" ]; then
        python scripts/detect_fillers.py "$video" "$subtitle" --execute
    fi
done
```

## 实际案例

### 案例 1: 处理采访视频

```
我有一个 30 分钟的采访视频 interview.mp4 和字幕 interview.srt，
请分析有多少语气词，然后生成去除语气词的版本
```

Claude 会：
1. 解析字幕，统计语气词数量
2. 显示将被移除的片段列表
3. 计算处理后视频时长
4. 生成 ffmpeg 命令
5. 询问确认后执行

### 案例 2: 预览后再处理

```
先分析 lecture.mp4 的字幕 lecture.srt，
告诉我有哪些语气词会被移除，让我确认后再处理
```

Claude 会：
1. 显示所有检测到的语气词片段
2. 显示时间轴和文本内容
3. 等待您确认
4. 确认后执行处理

### 案例 3: 保留特定片段

```
处理 presentation.mp4 和 presentation.srt，
但是保留 5:30-6:00 这段的所有内容，不要移除语气词
```

Claude 会调整逻辑，跳过指定时间段的处理。

## 输出文件说明

处理完成后会生成：

1. **{原文件名}_no_fillers.mp4** - 处理后的视频
2. **removed_segments.json** - 被移除片段的详细记录
   ```json
   {
     "input_video": "interview.mp4",
     "statistics": {
       "original_duration": "1800.00s",
       "final_duration": "1650.00s",
       "removed_duration": "150.00s",
       "filler_count": 45
     },
     "filler_segments": [...]
   }
   ```
3. **processing_log.txt** - 处理日志

## 常见问题

### Q: 如何避免误删正常词汇？

A: 脚本使用单词边界匹配，但仍可能误判。建议：
- 先运行分析模式查看结果
- 自定义语气词列表，移除容易误判的词
- 使用更精确的正则表达式

### Q: 处理大文件很慢怎么办？

A: 
- 使用 `-c copy` 避免重新编码（已默认）
- 分段处理长视频
- 使用更快的硬盘（SSD）

### Q: 字幕和视频不同步？

A: 确保：
- 字幕时间戳准确
- 视频和字幕是匹配的
- 使用原始视频文件（未压缩或转码）

### Q: 支持其他字幕格式吗？

A: 当前支持 SRT 和 VTT。其他格式需要先转换：
```bash
# 使用 ffmpeg 转换
ffmpeg -i subtitle.ass subtitle.srt
```

## 性能优化建议

1. **对于短视频（< 10 分钟）**：使用 select 方法
2. **对于长视频（> 10 分钟）**：使用 concat 方法（默认）
3. **批量处理**：使用脚本自动化
4. **质量要求高**：手动审核语气词列表后再处理

## 团队协作

将此 Skill 提交到 git：

```bash
git add .claude/skills/video-filler-word-remover/
git commit -m "Add video filler word remover skill"
git push
```

团队成员拉取后即可使用：

```bash
git pull
claude  # Skill 自动可用
```

## 联系与反馈

如有问题或建议，请：
- 查看 Claude Code 文档：https://code.claude.com/docs
- 提交 Issue 或改进建议
- 与团队成员分享使用经验