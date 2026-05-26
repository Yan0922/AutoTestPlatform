import os,json

from k2_asr_model_test.asr_test_code.test_cases.test_batch_infer import infer_batch_all
from k2_asr_model_test.asr_test_code.utils.new_wer_eval import get_wer
from k2_asr_model_test.asr_test_code.utils.comm import k2_model_update_json_reference
def k2_transfer_mult_jsonl_from_all(zh_result_jsonl_path,lang="zh"):
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
        zh_result_f_name = f'{name}_result.jsonl'
        
        zh_josnl_save_path = os.path.join(os.path.dirname(zh_result_jsonl_path), zh_result_f_name)
        with open(zh_josnl_save_path, 'w', encoding='utf-8') as json_file:
            json.dump(one_jsonl, json_file, ensure_ascii=False)
        zh_result_f_list.append(zh_result_f_name)
    return zh_result_f_list
def case_test_one_datases_all_lang(model_dir, datases_dir, save_dir):
    '''
    适用于一个模型和所有数据集（除外场测试的数据集）
    
    '''
    save_result_dir = infer_batch_all(model_dir, datases_dir, save_dir, False)
    # save_result_dir = "/home/guojun/workspace/T2_PRO_result/T2_PRO_20260115_120658"
    lang_list = ['zh-cn','en','es','ja','ko','th','fr','de','it','ar','ru']
    # lang_list = ['zh-cn']
    for i in lang_list:
        if i == 'zh-cn':
            src = f'zh.src'
        else:
            src = f'{i}.src'
        save_jsonl = os.path.join(save_result_dir, f'{i}.jsonl')
        print(f'save_jsonl:{save_jsonl}')
        if os.path.exists(save_jsonl):
            print(datases_dir)
            print(f'开始处理:{datases_dir}')
            if src != 'zh.src':
                print('test: outside_dataset but lang is not zh-cn...')
                k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                get_wer(os.path.join(save_result_dir, f'{i}_result.jsonl'), transcription_key=i)
            else:
                print('test: outside_dataset  and lang is zh-cn...')
                k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                zh_result_f_list = k2_transfer_mult_jsonl_from_all(save_jsonl.replace('.jsonl', '_result.jsonl'))
                for j in zh_result_f_list:
                    get_wer(os.path.join(save_result_dir, j), transcription_key=i)
    return save_result_dir


def case_wer_data_from_t2pro_txt(t2_jsonl_path, lang):
    zh_result_f_list = k2_transfer_mult_jsonl_from_all(t2_jsonl_path)
    for j in zh_result_f_list:
        get_wer(os.path.join(os.path.dirname(t2_jsonl_path), j), transcription_key=lang)
import re
def print_wer_files_simple_for_category(folder_path):
    """
    把输出的WER文件进行分类和排序，并打印每个分类下的文件名和对应的100-WER值。
    适用于8个分类：新录音、语音2601、T2pro-1-input、T2pro-2-input、T2pro-3-input、T2pro-1-output、T2pro-2-output、T2pro-3-output。
    数据来源于降噪后的文件夹中的WER文件。
    """
    # 定义8个分类
    categories = [
        "新录音",
        "语音2601", 
        "T2pro-1-input",
        "T2pro-2-input",
        "T2pro-3-input",
        "T2pro-1-output",
        "T2pro-2-output",
        "T2pro-3-output"
    ]
    
    # 为每个分类创建文件列表
    category_files = {category: [] for category in categories}
    
    # 收集并分类文件
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.wer'):
            for category in categories:
                if file_name.startswith(category):
                    category_files[category].append(file_name)
                    break
    
    # 对每个分类的文件进行排序
    for category in categories:
        category_files[category].sort()
    
    # 处理每个分类
    for category in categories:
        files = category_files[category]
        
        if not files:
            continue
        
        print(f"{category}:")
        
        # 打印文件名
        for file_name in files:
            # 显示简短文件名（去除路径）
            print(f"  {file_name}")
        
        print("100-wer:")
        
        # 打印对应的100-WER值
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 查找最后一行中的WER值
                lines = content.split('\n')
                if lines:
                    last_line = lines[-1]
                    match = re.search(r'WER:\s*([\d.]+)%', last_line)
                    
                    if match:
                        wer_value = float(match.group(1))
                        result = 100 - wer_value
                        print(f"  {result:.2f}")
                    else:
                        print("  N/A")
                else:
                    print("  N/A")
                    
            except Exception:
                print("  N/A")
        
        print()  # 空行分隔不同分类


def print_wer_for_t2pro_text(folder_path):    
    """
    简单地打印指定文件夹中所有.wer文件的文件名和对应的100-WER值，按文件名排序。
    适用于单个分类。比如：从设备终端取出来的文本转化jsonl后生成的wer
    """

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹 {folder_path} 不存在")
        exit()

    # 获取所有.wer文件
    wer_files = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.wer'):
            wer_files.append(file_name)

    if not wer_files:
        print(f"在文件夹 {folder_path} 中没有找到.wer文件")
        exit()

    # 按文件名排序
    wer_files.sort()

    # 输出文件名部分
    print("文件名")
    for file_name in wer_files:
        print(file_name)

    print("\n100-wer:")

    # 输出100-WER值
    for file_name in wer_files:
        file_path = os.path.join(folder_path, file_name)
        
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割成行
            lines = content.strip().split('\n')
            
            if lines:
                # 获取最后一行
                last_line = lines[-1]
                
                # 查找WER值
                match = re.search(r'WER:\s*([\d.]+)%', last_line)
                
                if match:
                    wer_value = float(match.group(1))
                    result = 100 - wer_value
                    print(f"{result:.2f}")
                else:
                    print("N/A")
            else:
                print("N/A")
                
        except Exception:
            print("ERROR")


if __name__ == '__main__':
    datases_dir = '/nasStore/guojun/T2_PRO/20260115_data'
    # 模型路径，给到具体模型的上一级目录
    model_dir = '/home/yanliuping/workspace_test/workspace_asr_test/k2_asr_model_test/model/0119/base'
    save_dir = '/home/yanliuping/workspace/model-test/k2_asr_model_test/asr_test_code/test_result/0119_t2pro'

    # 1、运行一个模型对所有数据集（降噪前，降噪后、三星、苹果）进行测试
    save_result_dir=case_test_one_datases_all_lang(model_dir, datases_dir, save_dir)
    print(f"结果保存在：{save_result_dir}")

    # 2、打印linux输出的准确率
    print_wer_files_simple_for_category(save_result_dir)



    # 3、计算T2 pro 设备上识别结果准确率
    # 使用在本地运行t2_pro_txt.py脚本生成的jsonl文件
    # case_wer_data_from_t2pro_txt("/home/yanliuping/workspace/model-test/k2_asr_model_test/asr_test_code/test_result/0119_t2pro/T2pro-1_0115.jsonl", "zh-cn")

    # 4、打印T2 pro 设备上识别结果的准确率
    # print_wer_for_t2pro_text("/home/yanliuping/workspace/model-test/k2_asr_model_test/asr_test_code/test_result/0119_t2pro")