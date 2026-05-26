



import json
import os

def k2_model_update_json_reference(json_file_path, scp_file_path):
    """
    读取JSON文件和SCP文件，根据name字段匹配并更新JSON中的reference字段
    
    Args:
        json_file_path (str): JSON文件路径
        scp_file_path (str): SCP文件路径
    """
    print(f"正在处理JSON文件: {json_file_path},{scp_file_path}")
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        json_data = []
        for line in json_file:
            if line.strip():  # 跳过空行
                json_data.append(json.loads(line))
    
    # 读取SCP文件并构建name到文本的映射
    scp_mapping = {}
    with open(scp_file_path, 'r', encoding='utf-8') as scp_file:
        for line in scp_file:
            if line.strip():  # 跳过空行
                # 分割name和文本内容
                parts = line.strip().split(' ', 1)
                if len(parts) >= 2:
                    name = parts[0]
                    text = parts[1].strip()
                    scp_mapping[name] = text
    
    # 更新JSON数据中的reference字段
    
    updated_count = 0
    for item in json_data:
        name = item.get('name')
        if name in scp_mapping:
            item['reference'] = scp_mapping[name]
            if json_file_path.endswith('zh.jsonl'):
                item['src_lang'] = 'zh-cn'
            updated_count += 1
    
    # 将更新后的数据写回JSON文件
    with open(json_file_path.replace('.jsonl','_result.jsonl'), 'w', encoding='utf-8') as json_file:
        for item in json_data:
            json_file.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"成功更新了 {updated_count} 条记录的reference字段")


def process_files(src_file, rst_file, output_file):
    """
    处理.src和.rst文件，生成JSONL格式的输出
    # 根据SRC和SRT文件生成JSONL文件，适用于微软等结果来测试
    
    Args:
        src_file: .src文件路径
        rst_file: .rst文件路径
        output_file: 输出JSONL文件路径
    """
    
    # 读取.src文件内容
    with open(src_file, 'r', encoding='utf-8') as f:
        src_lines = f.readlines()
    
    # 读取.rst文件内容
    with open(rst_file, 'r', encoding='utf-8') as f:
        rst_lines = f.readlines()
    
    # 检查两个文件行数是否一致
    if len(src_lines) != len(rst_lines):
        print(f"警告: 两个文件行数不一致！src文件有{len(src_lines)}行，rst文件有{len(rst_lines)}行")
    
    # 提取语言代码（从文件名中提取，如zh-CN -> zh-cn）
    lang_code = os.path.basename(src_file).split('.')[0].lower()
    
    # 创建输出文件
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for i, (src_line, rst_line) in enumerate(zip(src_lines, rst_lines)):
            src_line = src_line.strip()
            rst_line = rst_line.strip()
            
            if not src_line or not rst_line:
                continue
            
            try:
                # 处理.src文件行
                # 分割音频路径和文本
                src_parts = src_line.split(' ', 1)
                if len(src_parts) < 2:
                    print(f"警告: 跳过格式不正确的.src行 {i+1}: {src_line}")
                    continue
                
                audio_path = src_parts[0]
                reference_text = src_parts[1]
                
                # 从音频路径中提取文件名（不含扩展名）
                audio_filename = os.path.basename(audio_path)
                name = os.path.splitext(audio_filename)[0]
                
                # 处理.rst文件行
                # 按照.wav分割，取最后一个部分作为识别结果
                rst_parts = rst_line.split('.wav', 1)
                if len(rst_parts) < 2:
                    print(f"警告: 跳过格式不正确的.rst行 {i+1}: {rst_line}")
                    continue
                
                result_text = rst_parts[1].strip()
                
                # 构建JSON对象
                json_obj = {
                    "name": name,
                    "src_lang": lang_code,
                    "tgt_langs": [],
                    "reference": reference_text,
                    "result": {
                        "zh-cn": "",
                        "en": "",
                        "es": "",
                        "ja": "",
                        "ko": "",
                        "th": "",
                        "ar": "",
                        "de": "",
                        "fr": "",
                        "it": "",
                        "ru": ""
                    }
                }
                
                # 设置对应语言的识别结果
                json_obj["result"][lang_code] = result_text
                
                # 写入JSONL文件
                f_out.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
                
            except Exception as e:
                print(f"处理第 {i+1} 行时出错: {e}")
                print(f"src行: {src_line}")
                print(f"rst行: {rst_line}")
                continue


import os
import re
import pandas as pd
from openpyxl import Workbook

def extract_dataset_name(folder_name):
    """从文件夹名称中提取数据集名称"""
    if '_2025' in folder_name:
        return folder_name.split('_2025')[0]
    elif '_2024' in folder_name:
        return folder_name.split('_2024')[0]
    else:
        # 如果没有时间戳，返回原名称
        return folder_name

def process_single_dataset(folder_path):
    """处理单个数据集文件夹中的.wer文件"""
    # 定义语言顺序
    language_order = ['zh-cn', 'en', 'es', 'ja', 'ko', 'th', 'fr', 'de',"ru", 'it', 'ar',"ru"]
    
    # 存储结果的字典
    wer_data = {}
    sdi_data = {}
    
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith('wer'):
            # 提取语言名称
            if "_" in filename:
                language = filename.split('_')[0]
            else:
                language = filename[0:-4]

            print(f"正在处理 {language}")
            
            # 读取文件内容
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                with open(file_path, 'r', encoding='latin-1') as file:
                    lines = file.readlines()
            
            # 获取最后4行
            last_four_lines = lines[-4:] if len(lines) >= 4 else lines
            
            # 提取数据
            substitutions = None
            deletions = None
            insertions = None
            wer_value = None
            
            for line in last_four_lines:
                line = line.strip()
                if line.startswith('Substitutions:'):
                    substitutions = re.findall(r'\d+', line)[0]
                elif line.startswith('Deletions:'):
                    deletions = re.findall(r'\d+', line)[0]
                elif line.startswith('Insertions:'):
                    insertions = re.findall(r'\d+', line)[0]
                elif line.startswith('WER:'):
                    wer_value = line.split(':')[1].strip()
            
            # 存储到字典中
            if language =='zh':
                language = 'zh-cn'
            if wer_value:
                wer_data[language] = wer_value
            if substitutions and deletions and insertions:
                sdi_data[language] = f"{substitutions}/{deletions}/{insertions}"
            print(f"{language}: {wer_value}")
    # 按照指定的语言顺序整理数据
    ordered_wer_data = {}
    ordered_sdi_data = {}
    
    for lang in language_order:
        ordered_wer_data[lang] = wer_data.get(lang, 'N/A')
        ordered_sdi_data[lang] = sdi_data.get(lang, 'N/A')
    
    return ordered_wer_data, ordered_sdi_data

def create_combined_excel_report(result_dir):
    """创建包含所有数据集的Excel报告"""
    dir_name = result_dir.split('/')[-1]
    output_filename = os.path.join(result_dir, f"{dir_name}_combined_wer_analysis.xlsx")
    # 定义语言顺序
    language_order = ['zh-cn', 'en', 'es', 'ja', 'ko', 'th', 'fr', 'de', 'it', 'ar',"ru"]
    
    # 存储所有数据集的结果
    all_wer_data = {}
    all_sdi_data = {}
    dataset_names = []
    
    # 遍历结果目录下的所有文件夹
    for folder_name in os.listdir(result_dir):
        folder_path = os.path.join(result_dir, folder_name)
        if os.path.isdir(folder_path):
            # 检查文件夹中是否有.wer文件
            has_wer_files = any(filename.endswith('.wer') for filename in os.listdir(folder_path))
            if has_wer_files:
                dataset_name = extract_dataset_name(folder_name)
                print(f"处理数据集: {dataset_name} (文件夹: {folder_name})")
                
                # 处理单个数据集
                wer_data, sdi_data = process_single_dataset(folder_path)
                
                # 存储结果
                all_wer_data[dataset_name] = wer_data
                all_sdi_data[dataset_name] = sdi_data
                dataset_names.append(dataset_name)
    
    if not all_wer_data:
        print("错误: 在指定目录下没有找到包含.wer文件的文件夹!")
        return
    
    # 创建WER sheet的数据
    wer_sheet_data = []
    for lang in language_order:
        row = [lang]  # A列是语言
        for dataset in dataset_names:
            row.append(all_wer_data[dataset].get(lang, 'N/A'))
        wer_sheet_data.append(row)
    
    # 创建SDI sheet的数据
    sdi_sheet_data = []
    for lang in language_order:
        row = [lang]  # A列是语言
        for dataset in dataset_names:
            row.append(all_sdi_data[dataset].get(lang, 'N/A'))
        sdi_sheet_data.append(row)
    
    # 创建列标题
    wer_columns = ['Language'] + dataset_names
    sdi_columns = ['Language'] + dataset_names
    
    # 创建Excel文件
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        # 创建WER sheet
        wer_df = pd.DataFrame(wer_sheet_data, columns=wer_columns)
        wer_df.to_excel(writer, sheet_name='WER', index=False)
        
        # 创建SDI sheet
        sdi_df = pd.DataFrame(sdi_sheet_data, columns=sdi_columns)
        sdi_df.to_excel(writer, sheet_name='SDI', index=False)
    
    print(f"\n合并Excel报告已生成: {output_filename}")
    print(f"包含的数据集: {', '.join(dataset_names)}")
    print(f"每个数据集包含 {len(language_order)} 种语言")


def k2_transfer_zh_jsonl_from_all(zh_result_jsonl_path):
    # 读取原始包含多个中文的JSONL文件
    with open(zh_result_jsonl_path, 'r', encoding='utf-8') as json_file:
        src_json_data = []
        for line in json_file:
            if line.strip():  # 跳过空行
                src_json_data.append(json.loads(line))
        print(f"成功读取了 {len(src_json_data)} 条记录")
        print(src_json_data)
    zh_result_f_list = []
    # 创建新的JSONL文件
    for one_jsonl in src_json_data:
        name = one_jsonl["name"]
        zh_result_f_name = f'zh_{name}_result.jsonl'
        
        zh_josnl_save_path = os.path.join(os.path.dirname(zh_result_jsonl_path), zh_result_f_name)
        one_jsonl["src_lang"] = 'zh-cn'
        try:
            one_jsonl["result"]['zh-cn'] = one_jsonl["result"]['zh']
            # 删掉原来zh字段
            del one_jsonl["result"]['zh']
        except Exception:
            print(f"---------")
        with open(zh_josnl_save_path, 'w', encoding='utf-8') as json_file:
            json.dump(one_jsonl, json_file, ensure_ascii=False)
        zh_result_f_list.append(zh_result_f_name)
    return zh_result_f_list


# 使用示例
if __name__ == "__main__":
    # pass
    k2_model_update_json_reference("/home/guojun/workspace/en_2.jsonl","/home/guojun/workspace/en.src")
    
    '''
    # 推理后的数据测试必须要刷新结果，将ref刷新到jsonl中
    dir_path = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/1111_small/10min/20251112_114319'
    ref_dir = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/outside_dataset'
    import os
    for i in os.listdir(dir_path):
        if i.endswith('.jsonl'):
            lang = i.split('.')[0]
            k2_model_update_json_reference(os.path.join(dir_path,i),os.path.join(ref_dir,f'{lang}.src'))
    '''



    '''
    # 10分钟的外场测试中文需多做此步骤，把每个音频切分为单独JSON文件便于统计每个不同的场景下的CER
    def k2_transfer_zh_jsonl_from_all(zh_result_jsonl_path):
        # 读取原始包含多个中文的JSONL文件
        with open(zh_result_jsonl_path, 'r', encoding='utf-8') as json_file:
            src_json_data = []
            for line in json_file:
                if line.strip():  # 跳过空行
                    src_json_data.append(json.loads(line))
            print(f"成功读取了 {len(src_json_data)} 条记录")
            print(src_json_data)
        # 创建新的JSONL文件
        for one_jsonl in src_json_data:
            name = one_jsonl["name"]
            zh_result_f_name = f'zh_{name}_result.jsonl'
            zh_josnl_save_path = os.path.join(os.path.dirname(zh_result_jsonl_path), zh_result_f_name)
            one_jsonl["src_lang"] = 'zh-cn'
            one_jsonl["result"]['zh-cn'] = one_jsonl["result"]['zh']
            # 删掉原来zh字段
            del one_jsonl["result"]['zh']
            with open(zh_josnl_save_path, 'w', encoding='utf-8') as json_file:
                json.dump(one_jsonl, json_file, ensure_ascii=False)

    
    
    # zh_result_jsonl_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/1111_small/10min/20251112_114319/zh_result.jsonl"
    # k2_transfer_zh_jsonl_from_all(zh_result_jsonl_path)
    '''

    
    
    '''
    # # 根据SRC和SRT文件生成JSONL文件，适用于微软等结果来测试
    # dir_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_ms_30min"
    # save_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_ms_30min"
    # for i in os.listdir(dir_path):
    #     if i.endswith('es.src'):
    #         lang = i.split('.')[0]
    #         output_file = os.path.join(save_path,f'{lang}.jsonl')
    #         process_files(os.path.join(dir_path,i),os.path.join(dir_path,f'{lang}.rst'),output_file)
    #         print(f"处理完成！")
    #         print(f"JSONL文件已保存到: {output_file}")
            
    #         # 显示一些统计信息
    #         with open(output_file, 'r', encoding='utf-8') as f:
    #             lines = f.readlines()
    #             print(f"共生成 {len(lines)} 条JSON记录")
    '''



    '''
    生成excel报告的代码
    # # 设置结果目录路径
    # result_dir = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/1119_large'
    # # 检查目录是否存在
    # if not os.path.exists(result_dir):
    #     print("错误: 指定的目录不存在!")
    # # 生成合并的Excel报告
    # create_combined_excel_report(result_dir)
    # print("\n处理完成!")
    '''
    