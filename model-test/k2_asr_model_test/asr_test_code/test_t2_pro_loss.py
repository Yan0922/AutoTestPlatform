import os
import json


# 生成不同语言的JSONL的结果文件
def gen_jsonl_result(result_dir,ref_dir='/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/30_mins_dataset'):
    save_dir = f'{result_dir}_result'
    os.makedirs(save_dir,exist_ok=True)
    


    for lang_file in os.listdir(result_dir):
        if lang_file.endswith('.jsonl'):
            lang = lang_file.split('.')[0]
            with open(os.path.join(result_dir,lang_file),'r') as t2_pro_jsonl_f:
                t2_pro_jsonl_data = t2_pro_jsonl_f.readlines()
                # print(data)
                with open(os.path.join(save_dir,f'{lang}_result.jsonl'),'w') as save_result_jsonl_f:
                    if lang == 'zh-cn':
                        src_name = 'zh.src'
                    else:
                        src_name = f'{lang}.src'    
                    with open(os.path.join(ref_dir,src_name),'r') as src_ref_f:
                        ref_data = src_ref_f.readlines()
                        # print(src_data)
                        for t2_pro_line in t2_pro_jsonl_data:
                            text_model = {"name": "", "src_lang": "", "tgt_langs": [], "reference": "", "result": {"zh-cn": "", "en": "", "es": "", "ja": "", "ko": "", "th": "", "ar": "", "de": "", "fr": "", "it": "", "ru": ""}}
                            t2_pro_line = t2_pro_line.strip()
                            # print(type(t2_pro_line))
                            wav_name = t2_pro_line.split('.wav')[0].split('_')[-1]
                            # print(wav_name)
                            for ref_info in ref_data:
                                ref_num = ref_info.split(' ')[0]
                                if ref_num == wav_name:
                                    text_model['name'] = wav_name
                                    text_model['src_lang'] = lang
                                    space_index = ref_info.index(' ')
                                    reference = ref_info[space_index+1:]
                                    text_model['reference'] = reference.replace('\n','')
                                    text_model['result'][lang] = t2_pro_line.split('"result":"')[-1][0:-2]
                                    save_result_jsonl_f.write(json.dumps(text_model,ensure_ascii=False)+'\n')
                                    break

    return save_dir

def eval_wer_from_dir(save_dir):
    from k2_asr_model_test.asr_test_code.utils.new_wer_eval import get_wer
    jsonl_list = os.listdir(save_dir)
    for jsonl_file in jsonl_list:
        if jsonl_file.endswith('_result.jsonl'):
            lang = jsonl_file.split('_')[0]
            get_wer(os.path.join(save_dir,jsonl_file),transcription_key=lang)





result_dir = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/t2pro_loss_1011'
# save_dir = '/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/test_result/t2pro_loss_1011_result'
save_dir = gen_jsonl_result(result_dir)
eval_wer_from_dir(save_dir)


