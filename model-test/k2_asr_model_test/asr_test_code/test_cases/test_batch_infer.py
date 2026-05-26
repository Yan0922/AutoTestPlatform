import os,json,time
from k2_asr_model_test.asr_test_code.settings import MODEL_DIR,PRO_DPATH,TEST_DATA_DIR_Sota1,TEST_DATA_DIR_Sota2
import re
import shutil
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
                    # 去除<>等特殊符号
                    # if txt_predict_result.startswith('<'):
                    #     txt_predict_result = txt_predict_result[20:]
                    txt_predict_result = re.sub(r'<lang:[^>]+>', '', txt_predict_result)
                else:
                    # 如果没有空格，跳过这行
                    continue
                
                # 验证数字部分确实是数字
                # if not num.isdigit():
                #     continue
                    
                item['result'][lang] = txt_predict_result
                item["name"] = num
                f.write(json.dumps(item,ensure_ascii=False)+ "\n")
                
            except Exception as e:
                print(f"处理行时出错: {i}, 错误: {e}")
                continue
def infer_batch_all(modle_dir,data_dir,save_dir,debug=False,lang_list=None):
    # 将时间戳转换为时间元组
    time_tuple = time.localtime()
    print(time_tuple)
    # 格式化时间
    formatted_time = time.strftime("%Y%m%d_%H%M%S", time_tuple)
    print(formatted_time)
    datasets_name = data_dir.split('/')[-1]
    save_dir = os.path.join(save_dir,f"{datasets_name}_{formatted_time}")
    os.makedirs(save_dir,exist_ok=True)

    # 处理 multilingual 模型
    if lang_list:
        for i in os.listdir(modle_dir):
            if i.startswith('multilingual_'):
                orig_model_path=os.path.join(modle_dir,i)
                # 获取模型版本后缀，例如: large_v1.0.0.7
                suffix=i.replace('multilingual_','')
                for lang in lang_list:
                    # 构造新的模型目录名，例如: zh-cn_large_v1.0.0.7
                    new_model_name=f'{lang}_{suffix}'
                    new_model_path=os.path.join(modle_dir,new_model_name)

                    # 如果目录不存在，执行完整目录复制
                    if not os.path.exists(new_model_path):
                        print(f"正在复制模型: {i} -> {new_model_name}")
                        shutil.copytree(orig_model_path, new_model_path)
    # 推理循环，遍历所有模型
    for i in os.listdir(modle_dir):
        # 过滤掉原始的 multilingual 源文件，只处理生成好的 lang_xx 模型
        if i.lower().startswith('multilingual_') or '_v' not in i:
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

    '''推理单个数据集中单个语言'''
    modle_path = '/home/guojun/workspace/k2_asr_model_test/model/1029/en_base_v1.0.0.4'
    scp_path = '/home/guojun/workspace/en_2.scp'
    rst = infer_batch_lang(modle_path,scp_path)
    save_predict_result_as_jsonl(rst,'en','/home/guojun/workspace/en_2.jsonl')


    # ''' 批量推理模型中的语种'''
    # modle_dir = "/home/guojun/workspace/k2_asr_model_test/model/1125niko"
    # data_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/CV15"
    # save_dir = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/1125niko/CV15"
    # infer_batch_all(modle_dir,data_dir,save_dir,debug=False)