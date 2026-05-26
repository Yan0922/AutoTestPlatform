import os,json,time
from settings import MODEL_DIR,PRO_DPATH,TEST_DATA_DIR_Sota1,TEST_DATA_DIR_Sota2

def infer_batch_lang(modle_path,scp_path):
    os.chdir(PRO_DPATH)
    cmd = f'./testAsr {modle_path} {scp_path}'
    print(cmd)
    result  =  os.popen(cmd).read()
    # print(result)
    return result

def save_predict_result_as_jsonl(target_result,lang,save_path):
    target_result_list = target_result.split('\n')
    item = {
        "name": None,
        "src_lang": lang,
        "tgt_langs": [],
        "reference": None,
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
    with open(save_path,'w',encoding='utf-8') as f:
        for i in target_result_list:
            if not i or i.strip() == '':
                continue
            
            try:
                # 去除前后空白
                cleaned_line = i.strip()
                # 找到第一个空格的位置
                first_space_index = cleaned_line.find(' ')
                
                if first_space_index != -1:
                    num = cleaned_line[:first_space_index]
                    txt_predict_result = cleaned_line[first_space_index+1:].strip()
                else:
                    # 如果没有空格，跳过这行
                    continue
                
                # 验证数字部分确实是数字
                if not num.isdigit():
                    continue
                    
                item['result'][lang] = txt_predict_result
                item["name"] = num
                f.write(json.dumps(item,ensure_ascii=False)+ "\n")
            
            except Exception as e:
                print(f"处理行时出错: {i}, 错误: {e}")
                continue
def infer_batch_all(modle_dir,data_dir,save_dir,debug=False):
    # 将时间戳转换为时间元组
    time_tuple = time.localtime()
    print(time_tuple)
    # 格式化时间
    formatted_time = time.strftime("%Y%m%d_%H%M%S", time_tuple)
    print(formatted_time)
    save_dir = os.path.join(save_dir,formatted_time)
    os.makedirs(save_dir,exist_ok=True)
    for i in os.listdir(modle_dir):
        if i == "fr_small_v1.0.0.2":
            continue
        if '_v' not in i :
            continue
        # if debug:
        #     if not i.sartswith('es') or (not i.sartswith('zh')) or (not i.sartswith('en')):
        #         continue
        modle_path = os.path.join(modle_dir,i)
        lang = i.split('_')[0]
        scp_path = os.path.join(data_dir,f'{lang}.scp')
        if not os.path.exists(scp_path):
            print(f'{lang}.scp not exists')
            continue
        print(f'{lang} infer start...')
        result = infer_batch_lang(modle_path,scp_path)
        print(f"返回的result: {result}")
        sava_path = os.path.join(save_dir,f'{lang}.jsonl')
        save_predict_result_as_jsonl(result,lang,sava_path)
        print(f"{sava_path}保存成功！")
    return save_dir

if __name__ == '__main__':
    # pass
    # infer_batch_all(MODEL_DIR,TEST_DATA_DIR_Sota1,'/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result')
    # target_result = infer_batch_lang('/home/guojun/workspace/k2_asr_model_test/model/en_V1001','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/ten_en.scp')
    # save_predict_result_as_jsonl(target_result,'en','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/ten_en.jsonl')
    # infer_batch_all("/home/guojun/workspace/k2_asr_model_test/model/0916/small","/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/gf","/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_gf_small",debug=False)
    # modle_path = '/home/guojun/workspace/k2_asr_model_test/model/0916/small/it_small_v1.0.0.2'
    # scp_path = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/30_mins_dataset/it.scp'
    # rst = infer_batch_lang(modle_path,scp_path)
    # save_predict_result_as_jsonl(rst,'it','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_it/small/it.jsonl')

    ''' 批量推理模型中的语种'''
    modle_dir = "/home/guojun/workspace/k2_asr_model_test/model/0916/base"
    data_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/jianwei_tmp"
    save_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/jianwei1112/"
    infer_batch_all(modle_dir,data_dir,save_dir,debug=False)