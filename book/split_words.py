#!/usr/bin/env python3
import json
import os
import math

def split_unique_words():
    """
    将unique_words.json中的单词每1000个分割到对应的json文件中
    保持每个单词的JSON结构一致
    """

    # 文件路径
    input_file = os.path.expanduser('~/Desktop/myNote/unique_words.json')
    output_dir = os.path.expanduser('~/Desktop/myNote/split_words/')

    print("🔍 读取唯一单词文件...")
    print(f"📁 输入文件: {input_file}")
    print(f"📂 输出目录: {output_dir}")
    print("=" * 50)

    try:
        # 读取原始数据
        with open(input_file, 'r', encoding='utf-8') as f:
            words_data = json.load(f)

        total_words = len(words_data)
        words_per_file = 1000
        total_files = math.ceil(total_words / words_per_file)

        print(f"📊 总单词数量: {total_words}")
        print(f"📋 每文件单词数: {words_per_file}")
        print(f"📄 预计生成文件数: {total_files}")
        print("=" * 50)

        # 分割数据并保存
        for file_index in range(total_files):
            start_index = file_index * words_per_file
            end_index = min((file_index + 1) * words_per_file, total_words)

            # 获取当前分片的数据
            current_batch = words_data[start_index:end_index]

            # 重新分配wordRank（从1开始）
            for i, word_obj in enumerate(current_batch, 1):
                word_obj['wordRank'] = i

            # 生成文件名
            output_filename = f"words_{file_index + 1:03d}.json"
            output_path = os.path.join(output_dir, output_filename)

            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(current_batch, f, ensure_ascii=False, indent=2)

            # 显示进度
            actual_count = len(current_batch)
            progress = ((file_index + 1) / total_files) * 100
            print(f"✅ [{file_index + 1:3d}/{total_files}] {output_filename} - {actual_count} 个单词 ({progress:.1f}%)")

        print("=" * 50)
        print("✨ 分割完成!")
        print(f"📁 生成文件数量: {total_files}")
        print(f"📂 输出目录: {output_dir}")

        # 验证结果
        print("\n🔍 验证结果...")
        total_split_words = 0
        for file_index in range(total_files):
            filename = f"words_{file_index + 1:03d}.json"
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    split_data = json.load(f)
                    total_split_words += len(split_data)

        print(f"📊 原始单词数: {total_words}")
        print(f"📊 分割后总数: {total_split_words}")
        if total_words == total_split_words:
            print("✅ 验证成功: 数量一致!")
        else:
            print("❌ 验证失败: 数量不一致!")

        # 显示示例文件信息
        if total_files > 0:
            first_file = os.path.join(output_dir, "words_001.json")
            last_file = os.path.join(output_dir, f"words_{total_files:03d}.json")

            print(f"\n📄 示例文件信息:")
            with open(first_file, 'r', encoding='utf-8') as f:
                first_data = json.load(f)
                print(f"   words_001.json: {len(first_data)} 个单词")
                print(f"   首个单词: {first_data[0]['headWord']}")

            with open(last_file, 'r', encoding='utf-8') as f:
                last_data = json.load(f)
                print(f"   words_{total_files:03d}.json: {len(last_data)} 个单词")
                print(f"   末个单词: {last_data[-1]['headWord']}")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {input_file}")
    except json.JSONDecodeError as e:
        print(f"❌ 错误: JSON解析失败: {e}")
    except Exception as e:
        print(f"❌ 错误: 处理过程中出现问题: {e}")

if __name__ == "__main__":
    split_unique_words()