import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from k2_asr_model_test.asr_test_code.test_cases.test_batch_infer import infer_batch_all
from k2_asr_model_test.asr_test_code.utils.new_wer_eval import get_wer
from k2_asr_model_test.asr_test_code.settings import MODEL_DIR,PRO_DPATH,TEST_DATA_DIR_Sota1,TEST_DATA_DIR_Sota2,TEST_RESULT_DATA_DIR,TEST_DATA_DIR_30,TEST_DATA_DIR_CV15,TEST_DATA_DIR_gf,TEST_DATA_DIR_outside_dataset
from k2_asr_model_test.asr_test_code.utils.comm import k2_model_update_json_reference,create_combined_excel_report,k2_transfer_zh_jsonl_from_all

def case_test_one_datases_all_lang(model_dir, datases_dir, save_dir=TEST_RESULT_DATA_DIR,lang_list=None ):
    '''
    适用于一个模型和所有数据集（除外场测试的数据集）
    
    '''
    if lang_list is None:
        lang_list = ['zh-cn','en','es','ja','ko','th','fr','de','it','ar','ru']
    save_result_dir = infer_batch_all(model_dir, datases_dir, save_dir, False,lang_list=lang_list)
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
            if not datases_dir.endswith('outside_dataset'):
               print('test: other datasets...')
               k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
               get_wer(os.path.join(save_result_dir, f'{i}_result.jsonl'), transcription_key=i)
            else:
               if src != 'zh.src':
                   print('test: outside_dataset but lang is not zh-cn...')
                   k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                   get_wer(os.path.join(save_result_dir, f'{i}_result.jsonl'), transcription_key=i)
               else:
                   print('test: outside_dataset  and lang is zh-cn...')
                   k2_model_update_json_reference(save_jsonl, os.path.join(datases_dir, src))
                   zh_result_f_list = k2_transfer_zh_jsonl_from_all(save_jsonl.replace('.jsonl', '_result.jsonl'))
                   for i in zh_result_f_list:
                        get_wer(os.path.join(save_result_dir, i), transcription_key="zh-cn")

def run_multithread_test_cases(param_list):
    """
    多线程执行case_test_one_datases_all_lang函数
    
    Args:
        param_list: 参数列表，每个元素是一个包含(model_dir, datases_dir, save_dir)的元组
                    或者(model_dir, datases_dir)，此时使用默认的save_dir
    """
    with ThreadPoolExecutor(max_workers=len(param_list)) as executor:
        # 提交所有任务
        future_to_params = {}
        for params in param_list:
            # 处理参数：如果只有两个参数，使用默认save_dir；如果有三个参数，使用指定的save_dir
            if len(params) == 2:
                model_dir, datases_dir = params
                future = executor.submit(case_test_one_datases_all_lang, model_dir, datases_dir)
                future_to_params[future] = (model_dir, datases_dir, TEST_RESULT_DATA_DIR)
            elif len(params) == 3:
                model_dir, datases_dir, save_dir = params
                future = executor.submit(case_test_one_datases_all_lang, model_dir, datases_dir, save_dir)
                future_to_params[future] = (model_dir, datases_dir, save_dir)
            elif len(params) == 4:
                model_dir,datases_dir,save_dir,lang_list= params
                future = executor.submit(case_test_one_datases_all_lang, model_dir, datases_dir, save_dir, lang_list)
                future_to_params[future] = (model_dir, datases_dir, save_dir, lang_list)
        
        # 等待所有任务完成并处理结果
        for future in as_completed(future_to_params):
            model_dir, datases_dir, save_dir = future_to_params[future]
            try:
                result = future.result()
                # 打印 lang_list ，方便确认当前任务跑的是哪些语种
                lang_info = lang_list if lang_list else "All"
                print(f"任务完成: model_dir={model_dir}, datases_dir={datases_dir}, save_dir={save_dir}, langs={lang_info}")
            except Exception as exc:
                print(f"任务失败: model_dir={model_dir}, datases_dir={datases_dir}, save_dir={save_dir}, 错误: {exc}")

# 使用示例
if __name__ == "__main__":
    # 定义多组参数 - 支持两种格式
    result_dir = os.path.join(TEST_RESULT_DATA_DIR, '1209_ja_small_test') # 测试结果保存目录
    if not os.path.exists(result_dir):
        os.makedirs(result_dir,exist_ok=True)
    # TODO 如果是要测试多语种混合模型，需要修改 lang_list 这里，指定模型支持哪些语种
    lang_list = ['zh-cn','en','es','ja','ko','th','fr','de','it','ar','ru']
    param_list = [
        # 格式2: 指定所有三个参数
        # (os.path.join(MODEL_DIR, '1104', 'medium'), TEST_DATA_DIR_Sota1, "/custom/save/dir1"),
        # (os.path.join(MODEL_DIR, '1104', 'large'), TEST_DATA_DIR_Sota2, "/custom/save/dir2"),
        # ... 其他参数组合
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_30, result_dir,lang_list),
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_Sota1, result_dir,lang_list),
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_Sota2,result_dir,lang_list),
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_CV15,result_dir,lang_list),
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_gf,result_dir,lang_list),
        (os.path.join(MODEL_DIR, '1209', 'small'), TEST_DATA_DIR_outside_dataset ,result_dir,lang_list),
    ]
    
    # 执行多线程测试
    run_multithread_test_cases(param_list)
    # 生成测试Excel报告
    create_combined_excel_report(result_dir)
