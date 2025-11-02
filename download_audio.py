#!/usr/bin/env python3
import json
import os
import sys
import requests
import time
import argparse
from urllib.parse import quote
from pathlib import Path

class AudioDownloader:
    def __init__(self):
        self.base_dir = os.path.expanduser('~/Desktop/myNote')
        self.split_words_dir = os.path.join(self.base_dir, 'split_words')
        self.audio_dir = os.path.join(self.base_dir, 'audio_downloads')
        self.todo_file = os.path.join(self.base_dir, 'download_progress.json')

        # 确保目录存在
        os.makedirs(self.audio_dir, exist_ok=True)

        # 音频下载URL模板
        self.audio_url_template = "https://dict.youdao.com/dictvoice?audio={word}&type={type}"

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 初始化TODO列表
        self.load_or_create_todos()

    def load_or_create_todos(self):
        """加载或创建TODO列表"""
        if os.path.exists(self.todo_file):
            with open(self.todo_file, 'r', encoding='utf-8') as f:
                self.todos = json.load(f)
            print(f"📋 加载现有进度文件: {self.todo_file}")
            # 确保统计字段完整（向后兼容）
            self._ensure_statistics_fields()
        else:
            print("🆕 创建新的进度文件...")
            self.todos = self.create_initial_todos()
            self.save_todos()

    def _ensure_statistics_fields(self):
        """确保统计字段完整（向后兼容旧版本）"""
        if "statistics" not in self.todos:
            self.todos["statistics"] = {}

        # 添加缺失的字段
        default_stats = {
            "total_files": 0,
            "completed_files": 0,
            "total_words": 0,
            "downloaded_audios": 0,
            "failed_downloads": 0,
            "skipped_phrases": 0
        }

        for key, default_value in default_stats.items():
            if key not in self.todos["statistics"]:
                self.todos["statistics"][key] = default_value

        self.save_todos()

    def is_phrase(self, word):
        """检查是否为词组（包含空格或特殊字符）"""
        # 词组通常包含空格或连字符
        return ' ' in word or '-' in word

    def create_initial_todos(self):
        """创建初始TODO列表"""
        todos = {
            "files": [],
            "completed_files": [],
            "statistics": {
                "total_files": 0,
                "completed_files": 0,
                "total_words": 0,
                "downloaded_audios": 0,
                "failed_downloads": 0,
                "skipped_phrases": 0
            }
        }

        # 扫描split_words目录
        split_files = sorted([f for f in os.listdir(self.split_words_dir) if f.endswith('.json')])

        for filename in split_files:
            filepath = os.path.join(self.split_words_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    words_data = json.load(f)

                file_info = {
                    "filename": filename,
                    "word_count": len(words_data),
                    "status": "pending",  # pending, processing, completed, failed
                    "completed_words": 0,
                    "failed_words": 0,
                    "last_updated": None
                }

                todos["files"].append(file_info)
                todos["statistics"]["total_words"] += len(words_data)

            except Exception as e:
                print(f"❌ 读取文件失败 {filename}: {e}")

        todos["statistics"]["total_files"] = len(todos["files"])
        return todos

    def save_todos(self):
        """保存TODO列表"""
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(self.todos, f, ensure_ascii=False, indent=2)

    def download_audio(self, word, audio_type):
        """下载单个音频文件"""
        # 检查是否为词组，词组不需要下载
        if self.is_phrase(word):
            return False, "词组已跳过"

        try:
            # URL编码单词
            encoded_word = quote(word.lower())
            url = self.audio_url_template.format(word=encoded_word, type=audio_type)

            # 生成文件名
            type_name = "uk" if audio_type == 1 else "us"
            filename = f"{word}_{type_name}.mp3"
            filepath = os.path.join(self.audio_dir, filename)

            # 如果文件已存在，跳过
            if os.path.exists(filepath):
                return True, "已存在"

            # 下载音频
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # 检查响应内容
            if response.headers.get('content-type', '').startswith('audio') or len(response.content) > 1000:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True, "下载成功"
            else:
                return False, "无效音频"

        except requests.exceptions.RequestException as e:
            return False, f"网络错误: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def process_file(self, filename):
        """处理单个文件中的所有单词"""
        print(f"\n📂 处理文件: {filename}")
        print("=" * 50)

        # 找到文件信息
        file_info = None
        for f in self.todos["files"]:
            if f["filename"] == filename:
                file_info = f
                break

        if not file_info:
            print(f"❌ 未找到文件信息: {filename}")
            return False

        if file_info["status"] == "completed":
            print(f"✅ 文件已完成: {filename}")
            return True

        # 读取单词数据
        filepath = os.path.join(self.split_words_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                words_data = json.load(f)
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            file_info["status"] = "failed"
            self.save_todos()
            return False

        # 更新状态
        file_info["status"] = "processing"
        file_info["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')

        total_words = len(words_data)
        success_count = 0
        fail_count = 0
        skipped_count = 0

        print(f"📊 总单词数: {total_words}")

        for i, word_obj in enumerate(words_data, 1):
            word = word_obj.get('headWord', '').strip()
            if not word:
                continue

            # 检查是否为词组
            if self.is_phrase(word):
                print(f"[{i:4d}/{total_words}] 处理单词: {word}", end=" ")
                print("⏭️  词组已跳过")
                skipped_count += 1
                self.todos["statistics"]["skipped_phrases"] += 1
                continue

            print(f"[{i:4d}/{total_words}] 处理单词: {word}", end=" ")

            # 下载英式发音 (type=1)
            success_uk, msg_uk = self.download_audio(word, 1)
            time.sleep(0.5)  # 避免请求过快

            # 下载美式发音 (type=2)
            success_us, msg_us = self.download_audio(word, 2)
            time.sleep(0.5)  # 避免请求过快

            if success_uk and success_us:
                print("✅ 成功")
                success_count += 1
                self.todos["statistics"]["downloaded_audios"] += 2
            else:
                print(f"❌ 失败 (UK: {msg_uk}, US: {msg_us})")
                fail_count += 1
                self.todos["statistics"]["failed_downloads"] += 1

            # 每10个单词保存一次进度
            if i % 10 == 0:
                file_info["completed_words"] = success_count
                file_info["failed_words"] = fail_count
                self.save_todos()

        # 完成处理
        file_info["completed_words"] = success_count
        file_info["failed_words"] = fail_count
        file_info["status"] = "completed"
        file_info["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')

        # 更新统计
        if filename not in self.todos["completed_files"]:
            self.todos["completed_files"].append(filename)
            self.todos["statistics"]["completed_files"] += 1

        self.save_todos()

        print(f"\n✅ 文件处理完成!")
        print(f"   成功: {success_count} 个单词")
        print(f"   失败: {fail_count} 个单词")
        print(f"   跳过: {skipped_count} 个词组")

        return True

    def show_status(self, show_all_files=True):
        """显示当前状态"""
        stats = self.todos["statistics"]

        # 计算进度条
        total_files = stats['total_files']
        completed_files = stats['completed_files']
        file_progress = (completed_files / total_files * 100) if total_files > 0 else 0

        total_words = stats['total_words']
        completed_audios = stats['downloaded_audios']
        total_expected_audios = total_words * 2  # 每个单词2个音频
        audio_progress = (completed_audios / total_expected_audios * 100) if total_expected_audios > 0 else 0

        print("\n" + "=" * 70)
        print("🎵 有道词典音频下载器 - TODO进度状态")
        print("=" * 70)

        # 整体进度
        print(f"📊 整体进度:")
        print(f"   📁 文件进度: {self._draw_progress_bar(file_progress, 30)} {completed_files}/{total_files} ({file_progress:.1f}%)")
        print(f"   🎵 音频进度: {self._draw_progress_bar(audio_progress, 30)} {completed_audios}/{total_expected_audios} ({audio_progress:.1f}%)")

        print(f"\n📈 详细统计:")
        print(f"   📝 总单词数: {stats['total_words']:,}")
        print(f"   🎵 已下载音频: {stats['downloaded_audios']:,}")
        print(f"   ❌ 下载失败: {stats['failed_downloads']:,}")
        print(f"   ⏭️  已跳过词组: {stats.get('skipped_phrases', 0):,}")

        # 按状态分组显示文件
        print(f"\n📋 TODO列表状态:")

        status_groups = {
            "completed": [],
            "processing": [],
            "failed": [],
            "pending": []
        }

        for file_info in self.todos["files"]:
            status_groups[file_info["status"]].append(file_info)

        # 显示各状态的文件
        status_info = {
            "completed": ("✅ 已完成", "green"),
            "processing": ("🔄 处理中", "yellow"),
            "failed": ("❌ 失败", "red"),
            "pending": ("⏳ 待处理", "blue")
        }

        for status, (label, color) in status_info.items():
            files = status_groups[status]
            if files:
                print(f"\n   {label} ({len(files)} 个文件):")

                if show_all_files or status in ["processing", "failed"]:
                    # 完整显示处理中和失败的文件，其他状态可选择显示
                    for file_info in files:
                        word_progress = 0
                        if file_info['word_count'] > 0:
                            word_progress = (file_info['completed_words'] / file_info['word_count']) * 100

                        progress_bar = self._draw_progress_bar(word_progress, 20)

                        print(f"      📄 {file_info['filename']} {progress_bar} {file_info['completed_words']}/{file_info['word_count']}")

                        if file_info['last_updated']:
                            print(f"         ⏰ 最后更新: {file_info['last_updated']}")
                        if file_info['failed_words'] > 0:
                            print(f"         ❌ 失败数量: {file_info['failed_words']}")
                elif status == "completed" and len(files) > 5:
                    # 已完成的文件太多时只显示前几个和后几个
                    for file_info in files[:3]:
                        print(f"      ✅ {file_info['filename']} ({file_info['completed_words']}/{file_info['word_count']})")
                    if len(files) > 6:
                        print(f"      ... (省略 {len(files) - 6} 个文件)")
                    for file_info in files[-3:]:
                        print(f"      ✅ {file_info['filename']} ({file_info['completed_words']}/{file_info['word_count']})")
                elif status == "pending" and len(files) > 8:
                    # 待处理文件太多时只显示前几个
                    for file_info in files[:5]:
                        print(f"      ⏳ {file_info['filename']} ({file_info['word_count']} 个单词)")
                    print(f"      ... (还有 {len(files) - 5} 个待处理文件)")
                else:
                    # 正常显示
                    for file_info in files:
                        word_progress = 0
                        if file_info['word_count'] > 0:
                            word_progress = (file_info['completed_words'] / file_info['word_count']) * 100
                        print(f"      📄 {file_info['filename']} ({file_info['completed_words']}/{file_info['word_count']} - {word_progress:.1f}%)")

        print("=" * 70)

    def _draw_progress_bar(self, percentage, width=30):
        """绘制进度条"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"

    def get_next_pending_file(self):
        """获取下一个待处理的文件"""
        for file_info in self.todos["files"]:
            if file_info["status"] in ["pending", "failed"]:
                return file_info["filename"]
        return None

    def rescan_files(self):
        """重新扫描文件目录，添加新文件"""
        split_files = sorted([f for f in os.listdir(self.split_words_dir) if f.endswith('.json')])
        existing_files = [f["filename"] for f in self.todos["files"]]

        added_count = 0
        for filename in split_files:
            if filename not in existing_files:
                filepath = os.path.join(self.split_words_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        words_data = json.load(f)

                    file_info = {
                        "filename": filename,
                        "word_count": len(words_data),
                        "status": "pending",
                        "completed_words": 0,
                        "failed_words": 0,
                        "last_updated": None
                    }

                    self.todos["files"].append(file_info)
                    self.todos["statistics"]["total_words"] += len(words_data)
                    self.todos["statistics"]["total_files"] += 1
                    added_count += 1
                    print(f"📁 发现新文件: {filename} ({len(words_data)} 个单词)")

                except Exception as e:
                    print(f"❌ 读取新文件失败 {filename}: {e}")

        if added_count > 0:
            self.save_todos()
            print(f"✅ 添加了 {added_count} 个新文件")

        return added_count

    def run(self, target_files=None, num_files=1, rescan=False):
        """运行下载器"""
        print("🎵 有道词典音频下载器")
        print("=" * 50)
        print(f"📂 单词文件目录: {self.split_words_dir}")
        print(f"🎵 音频保存目录: {self.audio_dir}")
        print(f"📋 进度文件: {self.todo_file}")

        if rescan:
            print("\n🔍 重新扫描文件目录...")
            self.rescan_files()

        self.show_status()

        if target_files:
            # 处理指定文件
            for filename in target_files:
                if filename not in [f["filename"] for f in self.todos["files"]]:
                    print(f"❌ 文件不存在: {filename}")
                    continue
                self.process_file(filename)
        else:
            # 处理指定数量的待处理文件
            processed = 0
            while processed < num_files:
                next_file = self.get_next_pending_file()
                if not next_file:
                    print("\n✅ 所有文件都已处理完成!")
                    break

                self.process_file(next_file)
                processed += 1

        print("\n" + "=" * 50)
        self.show_status()

def main():
    parser = argparse.ArgumentParser(description='有道词典音频下载器')
    parser.add_argument('--files', '-f', nargs='+', help='指定要处理的文件名')
    parser.add_argument('--num', '-n', type=int, default=1, help='要处理的文件数量 (默认: 1)')
    parser.add_argument('--status', '-s', action='store_true', help='显示详细状态')
    parser.add_argument('--brief', '-b', action='store_true', help='显示简洁状态')
    parser.add_argument('--rescan', '-r', action='store_true', help='重新扫描文件目录')

    args = parser.parse_args()

    downloader = AudioDownloader()

    if args.status or args.brief:
        if args.rescan:
            downloader.rescan_files()
        show_all = not args.brief
        downloader.show_status(show_all_files=show_all)
    else:
        downloader.run(target_files=args.files, num_files=args.num, rescan=args.rescan)

if __name__ == "__main__":
    main()