mkdir -p .claude/skills/video-filler-word-remover/scripts
cd .claude/skills/video-filler-word-remover

# 将我创建的三个文件保存到对应位置：
# - SKILL.md
# - scripts/detect_fillers.py  
# - USAGE.md
```

### 第二步：通过 Claude Code 使用

启动 Claude Code 后，直接对话：
```
请帮我处理 interview.mp4 视频，移除字幕 interview.srt 中的所有语气词
```

Claude 会自动：
- 读取并分析字幕
- 识别语气词片段  
- 生成处理命令
- 执行并输出结果

## 🔧 高级特性

- **allowed-tools**: 限制只使用 Read、Write、Bash 工具
- **自定义语气词**：可编辑脚本中的词典
- **时间缓冲**：在语气词前后添加缓冲时间
- **片段合并**：自动合并间隔很小的片段

## 📊 输出示例
```
=== 视频处理分析 ===
输入视频: interview.mp4
字幕文件: interview.srt
输出视频: interview_no_fillers.mp4

统计信息:
  original_duration: 1800.00s
  final_duration: 1650.00s
  removed_duration: 150.00s
  filler_count: 45
  segments_kept: 23
