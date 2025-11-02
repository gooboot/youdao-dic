#!/usr/bin/env python3
import json
import os
from typing import Dict, List, Set

def extract_unique_words():
    """
    从当前目录中的所有JSON文件中提取唯一单词，
    保持原有的JSON格式，去除重复单词
    """

    # 获取当前目录中的所有JSON文件
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]

    if not json_files:
        print("未找到JSON文件")
        return

    unique_words: Dict[str, dict] = {}  # 使用字典存储唯一单词，key为headWord
    seen_words: Set[str] = set()  # 用于快速查重
    total_processed = 0

    print(f"找到 {len(json_files)} 个JSON文件，开始处理...")
    print("=" * 50)

    for file_index, json_file in enumerate(json_files, 1):
        # 显示文件处理进度
        file_progress = f"[{file_index}/{len(json_files)}]"
        print(f"{file_progress} 处理文件: {json_file}")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            words_data = []
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        word_obj = json.loads(line)
                        words_data.append(word_obj)
                    except json.JSONDecodeError:
                        continue

            file_word_count = len(words_data)
            file_unique_count = 0

            # 处理单个文件中的单词，显示进度
            for word_index, word_obj in enumerate(words_data, 1):
                if not isinstance(word_obj, dict):
                    continue

                head_word = word_obj.get('headWord', '').lower()  # 转为小写进行比较

                if head_word and head_word not in seen_words:
                    seen_words.add(head_word)
                    unique_words[head_word] = word_obj
                    file_unique_count += 1

                total_processed += 1

                # 每处理50个单词显示一次进度
                if word_index % 50 == 0 or word_index == file_word_count:
                    word_progress = (word_index / file_word_count) * 100
                    print(f"  📊 处理进度: {word_index}/{file_word_count} ({word_progress:.1f}%)", end='\r')

            print()  # 换行
            print(f"  ✅ 完成: 总单词 {file_word_count}, 新增唯一单词 {file_unique_count}")

        except FileNotFoundError:
            print(f"  ❌ 错误: 找不到文件 {json_file}")
        except Exception as e:
            print(f"  ❌ 错误: 处理 {json_file} 时出现问题: {e}")

    print("=" * 50)
    print("🔄 整理数据中...")

    # 将唯一单词转换为列表格式
    unique_words_list = list(unique_words.values())

    # 按照wordRank排序（如果存在）
    unique_words_list.sort(key=lambda x: x.get('wordRank', float('inf')))

    print("📝 重新分配序号...")
    # 重新分配wordRank，显示进度
    total_words = len(unique_words_list)
    for i, word_obj in enumerate(unique_words_list, 1):
        word_obj['wordRank'] = i

        # 每处理1000个单词显示一次进度
        if i % 1000 == 0 or i == total_words:
            progress = (i / total_words) * 100
            print(f"  进度: {i}/{total_words} ({progress:.1f}%)", end='\r')

    print()  # 换行

    # 保存到新文件
    output_dir = os.path.expanduser('~/Desktop/myNote/')
    os.makedirs(output_dir, exist_ok=True)  # 确保目录存在
    output_file = os.path.join(output_dir, 'unique_words.json')
    print(f"💾 保存到文件: {output_file}")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_words_list, f, ensure_ascii=False, indent=2)

        print("=" * 50)
        print("✨ 处理完成!")
        print(f"📁 处理的文件数量: {len(json_files)}")
        print(f"📊 原始单词总数: {total_processed}")
        print(f"🎯 唯一单词数量: {len(unique_words_list)}")
        if total_processed > 0:
            print(f"🗂️  去重比例: {((total_processed - len(unique_words_list)) / total_processed * 100):.1f}%")
        else:
            print("🗂️  去重比例: 0.0%")
        print(f"💾 结果已保存到: {output_file}")

    except Exception as e:
        print(f"❌ 错误: 保存文件时出现问题: {e}")

if __name__ == "__main__":
    extract_unique_words()