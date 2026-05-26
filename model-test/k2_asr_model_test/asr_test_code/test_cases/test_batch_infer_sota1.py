import os,json,time
from settings import MODEL_DIR,PRO_DPATH,TEST_DATA_DIR_Sota1,TEST_DATA_DIR_Sota2

def infer_batch_lang(modle_path,scp_path):
    os.chdir(PRO_DPATH)
    cmd = f'./testAsr {modle_path} {scp_path}'
    print(cmd)
    result  =  os.popen(cmd).read()
    print(result)
    return result

def save_predict_result_as_jsonl(target_result,lang,save_path):
    if not os.path.exists(save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if lang == 'zh':
        lang = 'zh-cn'
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
            if i == '':
                continue
            predict_txt_list = i.split('  ')
            num = predict_txt_list[0]
            txt_predict_result = predict_txt_list[-1]

            item['result'][lang] = txt_predict_result
            item["name"]= num
            f.write(json.dumps(item,ensure_ascii=False)+ "\n")
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
        if '_v' not in i :
            continue
        if debug:
            if not i.startswith('zh'):
                continue
        modle_path = os.path.join(modle_dir,i)
        lang = i.split('_')[0]
        scp_path = os.path.join(data_dir,f'{lang}.scp')
        if not os.path.exists(scp_path):
            print(f'{lang}.scp not exists')
            continue
        print(f'{lang} infer start...')
        result = infer_batch_lang(modle_path,scp_path)
        print(f"返回的result: {result}")
        if lang == 'zh':
            lang = 'zh-cn'
        sava_path = os.path.join(save_dir,f'{lang}.jsonl')
        save_predict_result_as_jsonl(result,lang,sava_path)
        print(f"{sava_path}保存成功！")
    return save_dir

if __name__ == '__main__':
#     # pass
#     # infer_batch_all(MODEL_DIR,TEST_DATA_DIR_Sota1,'/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result')
#     # target_result = infer_batch_lang('/home/guojun/workspace/k2_asr_model_test/model/en_V1001','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/ten_en.scp')
#     # save_predict_result_as_jsonl(target_result,'en','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/ten_en.jsonl')
#     # infer_batch_all("/home/guojun/workspace/k2_asr_model_test/model/0916/base","/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/gf","/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/0916_gf_base",debug=False)
    # modle_path = '/home/guojun/workspace/k2_asr_model_test/model/1029/en_base_v1.0.0.3'
    # scp_path = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/SOTA-1-WAV/en.scp'
    # rst = infer_batch_lang(modle_path,scp_path)
    # save_predict_result_as_jsonl(rst,'en','/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/V1003/en_sota1.jsonl')

    ''' 批量推理模型中的语种'''
    modle_dir = "/home/guojun/workspace/k2_asr_model_test/model/1104/base"
    data_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/SOTA-1-WAV"
    save_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/1104_asr_result/SOTA-1"
    infer_batch_all(modle_dir,data_dir,save_dir,debug=False)