import requests
import os
import zipfile
import shutil
import re
from urllib.parse import urljoin
from itertools import product
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# 一、模型下载模块
def get_model_category(model_name):
    parts = model_name.split('_')
    for part in parts[1:]:
        if part in ('base', 'small', 'large'):
            return part
    return 'other'

def get_model_language(model_name):
    """从模型名称中提取语言代码"""
    return model_name.split('_')[0]

def download_and_extract_model(model_name, zip_url, save_dir):
    zip_path = os.path.join(save_dir, f"{model_name}.zip")
    
    try:
        resp = requests.get(zip_url, timeout=60)
        if resp.status_code != 200:
            print(f"下载失败: {zip_url} (状态码 {resp.status_code})")
            return None
        
        with open(zip_path, 'wb') as f:
            f.write(resp.content)
        print(f"下载成功: {model_name}")
    except Exception as e:
        print(f"下载异常: {e}")
        return None

    category = get_model_category(model_name)
    cat_dir = os.path.join(save_dir, category)
    model_final_path = os.path.join(cat_dir, model_name)

    try:
        temp_dir = os.path.join(save_dir, f"{model_name}_temp_extract")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)

        items = os.listdir(temp_dir)
        if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
            inner = os.path.join(temp_dir, items[0])
            os.makedirs(cat_dir, exist_ok=True)
            if os.path.exists(model_final_path):
                shutil.rmtree(model_final_path)
            shutil.move(inner, model_final_path)
        else:
            os.makedirs(cat_dir, exist_ok=True)
            os.makedirs(model_final_path, exist_ok=True)
            for item in items:
                src = os.path.join(temp_dir, item)
                dst = os.path.join(model_final_path, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.move(src, dst)
                else:
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
        print(f"解压完成: {model_name}")
        return cat_dir
        
    except Exception as e:
        print(f"解压失败: {e}")
        return None

def get_latest_model_url(base_asr_url, lang, size):
    dir_url = urljoin(base_asr_url, f"{lang}/{size}/")
    try:
        resp = requests.get(dir_url, timeout=30)
        if resp.status_code != 200:
            print(f"目录不可访问: {dir_url}")
            return None, None
        
        matches = re.findall(r'<a href="([^"]*\.zip)">', resp.text)
        if not matches:
            print(f"目录为空: {dir_url}")
            return None, None

        def parse_ver(name):
            m = re.search(r'v(\d+)\.(\d+)\.(\d+)\.(\d+)', name)
            return tuple(map(int, m.groups())) if m else (0, 0, 0, 0)

        latest_zip = max(matches, key=parse_ver)
        model_name = latest_zip.replace('.zip', '')
        zip_url = urljoin(dir_url, latest_zip)
        return model_name, zip_url
    except Exception as e:
        print(f"获取最新模型失败 ({lang}/{size}): {e}")
        return None, None

def process_latest_mode(server_base, manual_model_names, save_dir):
    base_url = urljoin(server_base, "latest/")
    return [(name, urljoin(base_url, f"{name}.zip")) for name in manual_model_names]

def process_asr_mode(server_base, languages, sizes, save_dir):
    base_asr_url = urljoin(server_base, "asr/")
    tasks = []
    for lang, size in product(languages, sizes):
        model_name, zip_url = get_latest_model_url(base_asr_url, lang, size)
        if model_name and zip_url:
            tasks.append((model_name, zip_url))
        else:
            print(f"跳过: {lang}/{size}")
    return tasks

# 二、模型测试模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from k2_asr_model_test.asr_test_code.test_cases.test_batch_infer import infer_batch_all
from k2_asr_model_test.asr_test_code.utils.new_wer_eval import get_wer
from k2_asr_model_test.asr_test_code.settings import (
    TEST_DATA_DIR_Sota1, TEST_DATA_DIR_Sota2, TEST_DATA_DIR_30,
    TEST_DATA_DIR_CV15, TEST_DATA_DIR_gf, TEST_DATA_DIR_outside_dataset,
    TEST_RESULT_DATA_DIR
)
from k2_asr_model_test.asr_test_code.utils.comm import k2_model_update_json_reference, create_combined_excel_report, k2_transfer_zh_jsonl_from_all

def case_test_one_datases_all_lang(model_dir, datases_dir, save_dir=TEST_RESULT_DATA_DIR, langs=None):
    """
    适用于一个模型和一个数据集的完整测试（推理 + WER），支持过滤语言。
    
    Args:
        model_dir: 模型目录
        datases_dir: 数据集目录
        save_dir: 结果保存目录
        langs: 要测试的语言列表（如 ['zh', 'en']），如果 None 则测试所有语言
    """
    # 推理
    print(f"开始推理: {os.path.basename(datases_dir)}")
    save_result_dir = infer_batch_all(model_dir, datases_dir, save_dir, False)
    print(f"推理完成，结果存放在: {save_result_dir}")
    
    # 如果未指定语言，默认所有
    if langs is None:
        langs = ['zh', 'en', 'es', 'ja', 'ko', 'th', 'fr', 'de', 'it', 'ar', 'ru']
    
    # WER 计算（串行按语言）
    for lang in langs:
        test_lang = 'zh-cn' if lang == 'zh' else lang
        src = 'zh.src' if test_lang == 'zh-cn' else f'{test_lang}.src'
        save_jsonl = os.path.join(save_result_dir, f'{test_lang}.jsonl')
        
        if os.path.exists(save_jsonl):
            print(f"正在分析 WER -> 语言: {test_lang}, 目录: {os.path.basename(save_result_dir)}")
            print(f"正在处理JSON文件: {save_jsonl}, {os.path.join(datases_dir, src)}")
            
            if not datases_dir.endswith('outside_dataset'):
                # 普通数据集处理
                k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                get_wer(os.path.join(save_result_dir, f'{test_lang}_result.jsonl'), transcription_key=test_lang)
            else:
                # 外场测试数据集特殊处理
                k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                if test_lang != 'zh-cn':
                    get_wer(os.path.join(save_result_dir, f'{test_lang}_result.jsonl'), transcription_key=test_lang)
                else:
                    zh_result_f_list = k2_transfer_zh_jsonl_from_all(save_jsonl.replace('.jsonl', '_result.jsonl'))
                    for result_file in zh_result_f_list:
                        get_wer(os.path.join(save_result_dir, result_file), transcription_key="zh-cn")
            print(f"分析完成: {os.path.basename(datases_dir)} [{test_lang}]")
        else:
            print(f"跳过分析: {test_lang}.jsonl 不存在于 {save_result_dir}")

def run_multithread_test_cases(model_dir, datasets, base_result_dir, model_languages):
    """
    修改版：并行执行每个数据集的完整测试（推理 + WER）。
    
    Args:
        model_dir: 模型目录
        datasets: 数据集列表
        base_result_dir: 结果基础目录
        model_languages: 要测试的语言列表（如 ['zh', 'en']）
    """
    print(f"开始测试，模型目录: {model_dir}")
    print(f"涉及语言: {model_languages}")
    
    # 构建参数列表：每个数据集一个
    param_list = [(model_dir, dataset, base_result_dir, model_languages) for dataset in datasets]
    
    with ThreadPoolExecutor(max_workers=len(param_list)) as executor:
        future_to_params = {
            executor.submit(case_test_one_datases_all_lang, *params): params 
            for params in param_list
        }
        
        for future in as_completed(future_to_params):
            params = future_to_params[future]
            dataset_name = os.path.basename(params[1])
            try:
                future.result()
                print(f"数据集完成: {dataset_name}")
            except Exception as exc:
                print(f"数据集失败: {dataset_name}, 错误: {exc}")
    
    print("\n所有数据集推理及分析任务结束。")
    
if __name__ == "__main__":
    # TODO 运行代码之前需要确认使用什么方式来下载：asr/latest
    MODE = "latest"
    SERVER_BASE = "http://192.168.0.236:8000/k2/"
    # TODO 下载模型后的存放路径
    BASE_MODEL_DIR = "/home/yanliuping/workspace/model-test/k2_asr_model_test/model"
    
    # 获取当前日期
    today_str = datetime.now().strftime("%m%d_%H%M")
    MODEL_SAVE_DIR = os.path.join(BASE_MODEL_DIR, today_str)
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

    # 1、下载模型
    if MODE == "latest":
        # TODO 手动指定最新模型名称列表
        LATEST_MODEL_NAMES = ["en_base_v1.0.0.4"]
        task_list = process_latest_mode(SERVER_BASE, LATEST_MODEL_NAMES, MODEL_SAVE_DIR)
    elif MODE == "asr":
        # ASR_LANGUAGES = ["zh", "en", "es", "ja", "ko", "th", "fr", "de", "it", "ar", "ru"]
        # TODO 手动修改需要下载的语言和尺寸
        ASR_LANGUAGES = ["zh","ru"]
        ASR_SIZES = ["large"]
        task_list = process_asr_mode(SERVER_BASE, ASR_LANGUAGES, ASR_SIZES, MODEL_SAVE_DIR)
    else:
        raise ValueError("MODE 必须是 'latest' 或 'asr'")
    
    if not task_list:
        print("未生成任何下载任务")
        exit(0)

    downloaded_models = []
    for model_name, zip_url in task_list:
        print(f"处理模型: {model_name}")
        category_dir = download_and_extract_model(model_name, zip_url, MODEL_SAVE_DIR)
        if category_dir:
            downloaded_models.append((model_name, category_dir))

    if not downloaded_models:
        print("无模型下载成功")
        exit(1)

    # 2、定义测试数据集
    DATASET_DIRS = [
        TEST_DATA_DIR_30,
        TEST_DATA_DIR_Sota1,
        TEST_DATA_DIR_Sota2,
        TEST_DATA_DIR_CV15,
        TEST_DATA_DIR_gf,
        TEST_DATA_DIR_outside_dataset,
    ]

    # 3、按模型尺寸分组并测试
    # 按尺寸分组：base, small, large
    models_by_size = defaultdict(list)
    for model_name, category_dir in downloaded_models:
        size = get_model_category(model_name)
        models_by_size[size].append((model_name, category_dir))

    # 4、为每个尺寸创建统一目录并测试
    for size, models in models_by_size.items():
        print(f"\n{'='*60}")
        print(f"开始测试 {size} 尺寸的模型 ({len(models)}个)")
        
        # 创建统一的尺寸目录（如 1208_base）
        size_result_dir = os.path.join(TEST_RESULT_DATA_DIR, f"{today_str}_{size}")
        os.makedirs(size_result_dir, exist_ok=True)
        print(f"结果目录: {size_result_dir}")
        
        # 获取该尺寸下所有模型的语言
        languages_in_size = list(set([get_model_language(name) for name, _ in models]))
        print(f"将测试的语言: {languages_in_size}")
        
        # 获取第一个模型的category_dir（所有同尺寸模型在同一目录）
        first_model_name, first_category_dir = models[0]
        print(f"模型目录: {first_category_dir}")
        
        try:
            # 测试整个尺寸目录
            run_multithread_test_cases(first_category_dir, DATASET_DIRS, size_result_dir, languages_in_size)
            
            # 在尺寸目录中生成综合报告
            print(f"生成 {size} 尺寸的Excel报告...")
            create_combined_excel_report(size_result_dir)
            print(f"{size} 尺寸所有模型测试完成")
            
            
        except Exception as e:
            print(f"{size} 尺寸测试失败: {e}")
            import traceback
            traceback.print_exc()

    # 5、输出总结
    print(f"\n{'='*60}")
    print("所有尺寸模型测试完成")
    print(f"测试日期: {today_str}")
    print(f"模型保存位置: {MODEL_SAVE_DIR}")
    print(f"测试结果位置: {TEST_RESULT_DATA_DIR}")
