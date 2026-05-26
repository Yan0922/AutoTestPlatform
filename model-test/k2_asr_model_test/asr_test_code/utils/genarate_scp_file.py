import os
# import pandas as pd


# def load_test_data(excel_path):

#     # 读取整个 Excel（所有列作为字符串）
#     df = pd.read_excel(excel_path, dtype=str)
#     columns = df.columns.tolist()  # 转为列表
#     print("所有列名:", columns)
#     # 遍历每一列
#     all_data = {}
#     for column in df.columns:
#         column_data = df[column].tolist()  # 获取单列数据（Series格式）,转为列表
#         all_data[column] = column_data
#     return all_data

# def ganarate_scp(excel_path,wav_dir):
#     all_data = load_test_data(excel_path)
#     wav_list = []
#     ref_list = []
#     for index,i in enumerate(all_data):
#         if index==0:
#             continue
#         if index %2 == 1:
#             wav_list.append(wav_dir)
#         if index %2 == 0:
#             ref_list.append(wav_dir)
#     for index,lang_list in enumerate(wav_list):
#         lang_scp_file = f'./zh.scp'
#         with open(lang_scp_file,'w',encoding='utf-8')as f:
#             for name in lang_list:
#                 f.write(f'{index} {os.path.join(wav_dir,name)}\n')
from settings import TEST_DATA_DIR_30
import os


def ganarate_scp_src_form_list(wav_dir,list_file):
    '''
    适用于CV15 和GF 数据集 生成SRC 和   SCP文件用来测试
    参数:
    list_file: 测试数据集list文件路径，如test_de_lab.list
    wav_dir: 音频文件目录路径
    '''
    with open(list_file, 'r', encoding='utf-8') as f_list:
        f_list_data = f_list.readlines()
        lang = wav_dir.split('/')[-1].split('_')[0]
        with open(os.path.join(os.path.dirname(wav_dir),f'{lang}.scp'), 'w', encoding='utf-8') as f_scp:
            with open(os.path.join(os.path.dirname(wav_dir),f'{lang}.src'), 'w', encoding='utf-8') as f_src:
                for index,content in enumerate(f_list_data):

                    content = content.replace('\n', '')
                    content_list = content.split('.wav ')
                    ref = content_list[-1]
                    file_name = content_list[0].split('/')[-1] + ".wav"
                    file_path = os.path.join(wav_dir,file_name)
                    f_scp.write(f'{index} {file_path}\n')
                    f_src.write(f'{index} {ref}\n')


            
    
    
# ganarate_scp_src_form_list("/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/gf/de_wav","/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/gf/test_de_lab.list")




def ganarate_scp_src_form_dir(wav_dir):
    '''
    适用于30min测试数据集
    参数:
    wav_dir: 音频文件目录路径
    '''
    wav_dir_list = os.listdir(wav_dir)

    for wav_name in wav_dir_list:
        if not wav_name.endswith('wav'):
            continue
        lang_file_dir = os.path.join(wav_dir, wav_name)
        lang = wav_name[0:2]
        if lang != 'ja':
            continue
        df = pd.read_excel('/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/30_mins_dataset/ASR数据集-修正.xlsx', dtype=str,sheet_name=lang)
        column_data = df['文本'].tolist()



        with open(os.path.join(wav_dir,f'{wav_name[0:2]}.scp'), 'w', encoding='utf-8') as f_scp:
            with open(os.path.join(wav_dir,f'{wav_name[0:2]}.src'), 'w', encoding='utf-8') as f_src:
                with open(os.path.join(wav_dir,f'test_{wav_name[0:2]}_lab.list'), 'w', encoding='utf-8') as f_list:
                    for file in os.listdir(lang_file_dir):
                        file_path = os.path.join(lang_file_dir,file)
                        num = file.split('_')[-1].split('.')[0]
                        text = column_data[int(num)].replace('\n', '')
                        f_scp.write(f'{num} {file_path}\n')
                        f_src.write(f'{num} {text}\n')
                        f_list.write(f'{file_path} {text}\n')

# ganarate_scp_src_form_dir(TEST_DATA_DIR_30)


def ganarate_scp_src_form_dir_text(wav_dir):
    '''
    适用于其他数据集
    参数:
    wav_dir: 音频文件目录路径
    '''
    wav_dir_list = os.listdir(wav_dir)




    with open('./03.scp', 'w', encoding='utf-8') as f_scp:
        for file in wav_dir_list:
            file_path = os.path.join(wav_dir,file)

            num = file.split('.')[0]
            # text = column_data[int(num)].replace('\n', '')
            f_scp.write(f'{num} {file_path}\n')
            print(file_path)

ganarate_scp_src_form_dir_text("/nasStore/jianwei/T2Pro/移远算法验收/QDC552_声学算法客观测试记录_1121/03_安静环境_100cm_80db语音/英文wav/")

# # from moviepy.audio.io.AudioFileClip import AudioFileClip


# def convert_mp4_to_wav(input_mp4_path, output_wav_path=None, sample_rate=16000):
#     """
#     将MP4文件中的音频提取并转换为指定采样率的单通道WAV文件

#     参数:
#         input_mp4_path (str): 输入的MP4文件路径
#         output_wav_path (str, optional): 输出的WAV文件路径。如果为None，则自动生成
#         sample_rate (int, optional): 目标采样率，默认为16000Hz

#     返回:
#         str: 输出的WAV文件路径
#     """
#     # 如果未指定输出路径，则自动生成
#     if output_wav_path is None:
#         base_name = os.path.splitext(input_mp4_path)[0]
#         output_wav_path = f"{base_name}_16k_mono.wav"

#     try:
#         # 加载MP4文件中的音频
#         audio_clip = AudioFileClip(input_mp4_path)


#         # 导出为WAV文件
#         audio_clip.write_audiofile(
#             output_wav_path,
#             fps=sample_rate,
#             nbytes=2,  # 16-bit
#             codec='pcm_s16le',  # WAV格式
#             ffmpeg_params=['-ac', '1']  # 单声道
#         )

#         print(f"转换成功: {input_mp4_path} -> {output_wav_path}")
#         return output_wav_path

#     except Exception as e:
#         print(f"转换失败: {e}")
#         return None


# def convert_mp3_to_wav(input_mp3_path, output_wav_path=None, sample_rate=16000, channels=1):
#     """
#     将MP3文件转换为指定采样率和通道数的WAV文件

#     参数:
#         input_mp3_path (str): 输入的MP3文件路径
#         output_wav_path (str, optional): 输出的WAV文件路径。如果为None，则自动生成
#         sample_rate (int, optional): 目标采样率，默认为16000Hz
#         channels (int, optional): 目标通道数，1为单声道，2为立体声，默认为1

#     返回:
#         str: 输出的WAV文件路径
#     """
#     # 如果未指定输出路径，则自动生成
#     if output_wav_path is None:
#         base_name = os.path.splitext(input_mp3_path)[0]
#         output_wav_path = f"{base_name}_16k_mono.wav"

#     try:
#         # 加载MP3文件
#         audio = AudioSegment.from_mp3(input_mp3_path)

#         # 设置采样率和通道数
#         audio = audio.set_frame_rate(sample_rate)
#         audio = audio.set_channels(channels)

#         # 导出为WAV文件
#         audio.export(output_wav_path, format="wav")

#         print(f"转换成功: {input_mp3_path} -> {output_wav_path}")
#         return output_wav_path

#     except Exception as e:
#         print(f"转换失败: {e}")
#         return None

# def convert_m4a_to_wav(input_m4a_path, output_wav_path=None, sample_rate=16000):
#     """
#     将M4A文件转换为指定采样率的单通道WAV文件

#     参数:
#         input_m4a_path (str): 输入的M4A文件路径
#         output_wav_path (str, optional): 输出的WAV文件路径。如果为None，则自动生成
#         sample_rate (int, optional): 目标采样率，默认为16000Hz

#     返回:
#         str: 输出的WAV文件路径
#     """
#     # 如果未指定输出路径，则自动生成
#     if output_wav_path is None:
#         base_name = os.path.splitext(input_m4a_path)[0]
#         output_wav_path = f"{base_name}_16k_mono.wav"

#     try:
#         # 加载M4A文件
#         audio = AudioSegment.from_file(input_m4a_path, format="m4a")

#         # 设置为单声道
#         audio = audio.set_channels(1)

#         # 设置采样率
#         audio = audio.set_frame_rate(sample_rate)

#         # 导出为WAV文件
#         audio.export(
#             output_wav_path,
#             format="wav",
#             parameters=["-ac", "1", "-ar", str(sample_rate)]
#         )

#         print(f"转换成功: {input_m4a_path} -> {output_wav_path}")
#         return output_wav_path

#     except Exception as e:
#         print(f"转换失败: {e}")
#         return None


# # import wave
# # import audioop
# # from pydub import AudioSegment
# # import subprocess


# def convert_wav_to_16k_mono(input_path, output_path=None, sample_rate=16000, verbose=True):
#     """
#     将WAV文件转换为16kHz单通道WAV文件

#     参数:
#         input_path (str): 输入的WAV文件路径
#         output_path (str, optional): 输出的WAV文件路径，默认自动生成
#         sample_rate (int, optional): 目标采样率(Hz)，默认16000
#         verbose (bool, optional): 是否打印转换信息，默认True

#     返回:
#         str: 转换后的WAV文件路径，失败返回None
#     """
#     # 检查输入文件是否存在
#     if not os.path.isfile(input_path):
#         if verbose:
#             print(f"错误：输入文件不存在 - {input_path}")
#         return None

#     # 验证输入文件是否为WAV格式
#     try:
#         with wave.open(input_path, 'rb') as wav_file:
#             pass
#     except:
#         if verbose:
#             print(f"错误：输入文件不是有效的WAV格式 - {input_path}")
#         return None

#     # 自动生成输出路径（如果未提供）
#     if output_path is None:
#         base_dir = os.path.dirname(input_path)
#         base_name = os.path.splitext(os.path.basename(input_path))[0]
#         output_path = os.path.join(base_dir, f"{base_name}_16k_mono.wav")

#     try:
#         # 方法1：使用pydub转换（推荐）
#         try:
#             audio = AudioSegment.from_wav(input_path)

#             # 如果已经是单声道且16kHz，直接复制文件
#             if audio.frame_rate == sample_rate and audio.channels == 1:
#                 if verbose:
#                     print(f"文件已经是16kHz单声道WAV，直接复制: {input_path}")
#                 audio.export(output_path, format="wav")
#                 return output_path

#             # 转换为单声道和指定采样率
#             audio = audio.set_frame_rate(sample_rate).set_channels(1)
#             audio.export(output_path, format="wav")

#             if verbose:
#                 print(f"成功转换: {input_path} -> {output_path}")
#             return output_path

#         # 如果pydub方法失败，尝试使用ffmpeg直接调用
#         except Exception as pydub_error:
#             if verbose:
#                 print(f"pydub转换失败，尝试使用ffmpeg直接转换: {str(pydub_error)}")

#             ffmpeg_cmd = [
#                 'ffmpeg',
#                 '-y',  # 覆盖输出文件
#                 '-i', input_path,
#                 '-ac', '1',  # 单声道
#                 '-ar', str(sample_rate),  # 采样率
#                 '-acodec', 'pcm_s16le',  # 16-bit PCM编码
#                 output_path
#             ]

#             # 运行ffmpeg命令
#             result = subprocess.run(
#                 ffmpeg_cmd,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 text=True
#             )

#             if result.returncode != 0:
#                 raise Exception(f"ffmpeg转换失败: {result.stderr}")

#             if verbose:
#                 print(f"ffmpeg转换成功: {input_path} -> {output_path}")
#             return output_path

#     except Exception as e:
#         if verbose:
#             print(f"转换失败: {str(e)}")
#         # 删除可能创建的不完整输出文件
#         if os.path.exists(output_path):
#             try:
#                 os.remove(output_path)
#             except:
#                 pass
#         return None


# def convert_pcm_to_wav(input_pcm_path, output_wav_path=None,
#                        sample_rate=16000, channels=1, sample_width=2,
#                        original_rate=16000, original_channels=1):
#     """
#     将PCM文件转换为16kHz单通道WAV文件

#     参数:
#         input_pcm_path (str): 输入的PCM文件路径
#         output_wav_path (str, optional): 输出的WAV文件路径
#         sample_rate (int): 目标采样率(默认16000Hz)
#         channels (int): 目标通道数(默认1)
#         sample_width (int): 采样宽度(字节数，默认2表示16-bit)
#         original_rate (int): 原始采样率(默认44100Hz)
#         original_channels (int): 原始通道数(默认2)

#     返回:
#         str: 输出的WAV文件路径
#     """
#     # 自动生成输出路径
#     if output_wav_path is None:
#         base_name = os.path.splitext(input_pcm_path)[0]
#         output_wav_path = f"{base_name}_16k_mono.wav"

#     try:
#         # 方法1：使用pydub转换（推荐）
#         try:
#             # 读取PCM数据
#             with open(input_pcm_path, 'rb') as pcm_file:
#                 pcm_data = pcm_file.read()

#             # 创建AudioSegment对象
#             audio = AudioSegment(
#                 data=pcm_data,
#                 sample_width=sample_width,
#                 frame_rate=original_rate,
#                 channels=original_channels
#             )

#             # 转换采样率和通道数
#             audio = audio.set_frame_rate(sample_rate).set_channels(channels)

#             # 导出为WAV
#             audio.export(output_wav_path, format="wav")
#             print(f"转换成功: {input_pcm_path} -> {output_wav_path}")
#             return output_wav_path

#         # 方法2：使用wave和audioop（不依赖pydub）
#         except Exception as e:
#             print(f"pydub转换失败，尝试原生方法: {e}")

#             with open(input_pcm_path, 'rb') as pcm_file:
#                 pcm_data = pcm_file.read()

#             # 转换采样率（需要知道原始采样率）
#             if original_rate != sample_rate:
#                 pcm_data = audioop.ratecv(
#                     pcm_data,
#                     sample_width,
#                     original_channels,
#                     original_rate,
#                     sample_rate,
#                     None
#                 )[0]

#             # 转换单声道（如果是立体声）
#             if original_channels != 1 and channels == 1:
#                 pcm_data = audioop.tomono(pcm_data, sample_width, 1, 1)

#             # 写入WAV文件
#             with wave.open(output_wav_path, 'wb') as wav_file:
#                 wav_file.setnchannels(channels)
#                 wav_file.setsampwidth(sample_width)
#                 wav_file.setframerate(sample_rate)
#                 wav_file.writeframes(pcm_data)

#             print(f"转换成功: {input_pcm_path} -> {output_wav_path}")
#             return output_wav_path

#     except Exception as e:
#         print(f"转换失败: {e}")
#         # 删除可能生成的不完整文件
#         if os.path.exists(output_wav_path):
#             os.remove(output_wav_path)
#         return None


def read_excel_by_sheet_pandas(file_path,target_sheet_name=None):
    """
    使用pandas读取Excel文件，按Sheet返回所有行的数据

    :param file_path: Excel文件路径
    :return: 字典，key为sheet名，value为该sheet的DataFrame
    """
    excel_file = pd.ExcelFile(file_path)
    result = {}
    if target_sheet_name:
        df = excel_file.parse(target_sheet_name)
        # 将DataFrame转换为行数据列表
        rows_data = df.values.tolist()
        # 如果需要包含列名，可以使用以下代码
        # rows_data = [df.columns.tolist()] + df.values.tolist()
        result[target_sheet_name] = rows_data
        return result
    for sheet_name in excel_file.sheet_names:
        df = excel_file.parse(sheet_name)
        # 将DataFrame转换为行数据列表
        rows_data = df.values.tolist()
        # 如果需要包含列名，可以使用以下代码
        # rows_data = [df.columns.tolist()] + df.values.tolist()
        result[sheet_name] = rows_data

    return result




# # # 使用示例
# # file_path = './test_data/ASR数据集.xlsx'
# # data = read_excel_by_sheet_pandas(file_path)
# #
# # for sheet_name, rows in data.items():
# #     if sheet_name == 'ar' or sheet_name == 'de':
# #         continue
# #     src_dir_path = os.path.join('./test_data/', sheet_name)
# #
# #     trg_dir_path = os.path.join('./test_data/',f'{sheet_name}_wav')
# #     os.makedirs(trg_dir_path,exist_ok=True)
# #     print(f"Sheet: {sheet_name}")
# #
# #     for row in rows:
# #         # print(row)
# #         src_file_name = row[1]
# #
# #         src_path = os.path.join(src_dir_path,src_file_name)
# #         wav_name = f'{sheet_name}_{row[0]}.wav'
# #
# #         wav_path = os.path.join(trg_dir_path,wav_name)
# #         print(wav_name)
# #         if src_file_name.endswith('mp4'):
# #             convert_mp4_to_wav(src_path, wav_path)
# #         if src_file_name.endswith('mp3'):
# #             # 转换MP3到wav
# #             convert_mp3_to_wav(src_path, wav_path)
# #         # print(wav_name)
# #         if src_file_name.endswith('m4a'):
# #             convert_m4a_to_wav(src_path, wav_path)
# #
# #         if src_file_name.endswith('mav'):
# #             convert_wav_to_16k_mono(src_path, wav_path)
# #
# #         if src_file_name.endswith('pcm'):
# #             convert_pcm_to_wav(src_path, wav_path)


import os,json,shutil
from settings import TEST_DATA_DIR_Sota1,TEST_DATA_DIR_Sota2
def sota_data_convert_scp_src_no_zh(sota_json_path):
    """
    将SOTA数据集的json文件转换为scp文件

    :param sota_json_path: SOTA数据集的json文件路径
    :return: None
    """
    with open(sota_json_path, "r", encoding='utf-8') as fin:
        sota_json_data = []
        for line in fin:
            sota_json = json.loads(line)
            sota_json_data.append(sota_json)
    print(len(sota_json_data))
    

    sota_json_dir = os.path.dirname(sota_json_path)
    for i in os.listdir(sota_json_dir):
        if i.endswith('_src'):
            lang_name = i.split('_')[0]
            new_wav_dir = os.path.join(sota_json_dir, f'{lang_name}_wav')
            print(new_wav_dir)
            os.makedirs(new_wav_dir, exist_ok=True)
            with open(os.path.join(sota_json_dir, lang_name+'.src'), "w", encoding='utf-8') as f_src:
                with open(os.path.join(sota_json_dir, lang_name+'.scp'), "w", encoding='utf-8') as f_scp:
                
                    for j in sota_json_data:

                        if lang_name == j['language']:
                            print(j)
                            id_num = j['id']
                            wav_src_name = j['wav_path'].split('/')[-1]
                            wav_path = os.path.join(sota_json_dir, i, wav_src_name)
                            ref = j.get('text')
                            
                            print(wav_path)

                            new_wav_path = os.path.join(new_wav_dir, f'{id_num}.wav')
                            old_wav_path = os.path.join(sota_json_dir, i, wav_src_name)
                            f_src.write(f'{id_num} {ref}\n')
                            f_scp.write(f'{id_num} {new_wav_path}\n')
                            
                            shutil.copy(old_wav_path,new_wav_path)
                            


def sota_data_convert_scp_src(sota_json_path,sota=1):
    """
    将SOTA数据集的json文件转换为scp文件

    :param sota_json_path: SOTA数据集的json文件路径
    :return: None
    """
    if sota == 1:
        TEST_DATA_DIR_Sota = TEST_DATA_DIR_Sota1
    else:
        TEST_DATA_DIR_Sota = TEST_DATA_DIR_Sota2
    with open(sota_json_path, "r", encoding='utf-8') as fin:
        sota_json_data = []
        for line in fin:
            sota_json = json.loads(line)
            sota_json_data.append(sota_json)
    print(len(sota_json_data))
    zh_wav_dir = os.path.join(TEST_DATA_DIR_Sota, f'zh_wav')
    en_wav_dir = os.path.join(TEST_DATA_DIR_Sota, f'en_wav')
    es_wav_dir = os.path.join(TEST_DATA_DIR_Sota, f'es_wav')
    ja_wav_dir = os.path.join(TEST_DATA_DIR_Sota, f'ja_wav')
    with open(os.path.join(TEST_DATA_DIR_Sota, 'zh.src'), "w", encoding='utf-8') as zh_f_src:
        with open(os.path.join(TEST_DATA_DIR_Sota, 'zh.scp'), "w", encoding='utf-8') as zh_f_scp:
            with open(os.path.join(TEST_DATA_DIR_Sota, 'en.src'), "w", encoding='utf-8') as en_f_src:
                with open(os.path.join(TEST_DATA_DIR_Sota, 'en.scp'), "w", encoding='utf-8') as en_f_scp:
                    with open(os.path.join(TEST_DATA_DIR_Sota, 'es.src'), "w", encoding='utf-8') as es_f_src:
                        with open(os.path.join(TEST_DATA_DIR_Sota, 'es.scp'), "w", encoding='utf-8') as es_f_scp:
                            with open(os.path.join(TEST_DATA_DIR_Sota, 'ja.src'), "w", encoding='utf-8') as ja_f_src:
                                with open(os.path.join(TEST_DATA_DIR_Sota, 'ja.scp'), "w", encoding='utf-8') as ja_f_scp:



                                    for j in sota_json_data:
                                        lang_name = j['language']
                                        id_num = j['id']
                                        wav_src_name = j['wav_path'].split('/')[-1]
                                        ref = j.get('text')
                                        if lang_name == 'zh':
                                            new_wav_dir = zh_wav_dir
                                            src_file = zh_f_src
                                            scp_file = zh_f_scp
                                        elif lang_name == 'en':
                                            new_wav_dir = en_wav_dir
                                            src_file = en_f_src
                                            scp_file = en_f_scp
                                        elif lang_name == 'es':
                                            new_wav_dir = es_wav_dir
                                            src_file = es_f_src
                                            scp_file = es_f_scp
                                        elif lang_name == 'ja':
                                            new_wav_dir = ja_wav_dir
                                            src_file = ja_f_src
                                            scp_file = ja_f_scp

                                        src_wav_path = os.path.join(TEST_DATA_DIR_Sota, 'all_src', wav_src_name)
                                        new_wav_path = os.path.join(new_wav_dir, f'{id_num}.wav')
                                        src_file.write(f'{id_num} {ref}\n')
                                        scp_file.write(f'{id_num} {new_wav_path}\n')
                                        shutil.copy(src_wav_path,new_wav_path)
        

def process_audio_list(input_file, src_output_file, scp_output_file, base_path):
    """
    处理音频列表文件，生成.src和.scp文件
    
    Args:
        input_file: 输入文件路径
        src_output_file: 输出文本文件路径
        scp_output_file: 输出音频路径文件路径
        base_path: 音频文件的基础路径（可选）
    """
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(src_output_file, 'w', encoding='utf-8') as f_src, \
         open(scp_output_file, 'w', encoding='utf-8') as f_scp:
        
        index = 0  # 从0开始的索引
        
        for line in f_in:
            line = line.strip()
            if not line:
                continue  # 跳过空行
                
            # 按照.wav进行分割
            parts = line.split('.wav')
            if len(parts) < 2:
                print(f"警告: 跳过格式不正确的行: {line}")
                continue
                
            # 获取音频文件名和文本
            audio_path_part = parts[0].strip()
            text = parts[1].strip()
            
            # 按照/进行分割，获取音频文件名
            path_parts = audio_path_part.split('/')
            audio_filename = path_parts[-1] + '.wav'  # 重新添加.wav扩展名
            
            # 构建完整的音频文件路径
            full_audio_path = os.path.join(base_path, audio_filename)
            if not os.path.exists(full_audio_path):
                print(f"警告: 音频文件不存在: {full_audio_path}")
                continue
            
            # 写入.src文件 (索引 + 文本)
            f_src.write(f"{index} {text}\n")
            
            # 写入.scp文件 (索引 + 音频文件路径)
            f_scp.write(f"{index} {full_audio_path}\n")
            
            index += 1  # 增加索引

def merge_scp_src_to_list(scp_file, src_file, output_file):
    """
    将.scp和.src文件按索引合并成.list文件
    
    Args:
        scp_file: .scp文件路径
        src_file: .src文件路径  
        output_file: 输出的.list文件路径
    """
    # 读取.scp文件内容
    scp_data = {}
    with open(scp_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(' ', 1)  # 只分割第一个空格
                if len(parts) == 2:
                    index, path = parts
                    scp_data[index] = path
    
    # 读取.src文件内容
    src_data = {}
    with open(src_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(' ', 1)  # 只分割第一个空格
                if len(parts) == 2:
                    index, text = parts
                    src_data[index] = text
    
    # 确保两个文件有相同的索引
    if set(scp_data.keys()) != set(src_data.keys()):
        print("警告: .scp和.src文件的索引不完全一致")
    
    # 按索引顺序合并数据并写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f_out:
        # 按索引排序（如果需要保持顺序）
        for index in sorted(scp_data.keys(), key=lambda x: int(x)):
            if index in src_data:
                line = f"{scp_data[index]} {src_data[index]}\n"
                f_out.write(line)
            else:
                print(f"警告: 索引 {index} 在.src文件中不存在")
    
    print(f"合并完成！输出文件: {output_file}")



# if __name__ == "__main__":
#     base_audio_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/30_mins_dataset"
#     for i in os.listdir(base_audio_path):
#         print(i)
#         # if i.endswith('.scp'):
#         if i == 'ja.scp':
#             lang = i.split('.')[0]
#             src = f'{lang}.src'
#             scp = f'{lang}.scp'
#             list_name = f'test_{lang}_lab.list'
#             merge_scp_src_to_list(os.path.join(base_audio_path,scp), os.path.join(base_audio_path,src), os.path.join(base_audio_path,list_name))
#             print(f'{lang} 生成list ---done---')




    
    # # 音频文件基础路径（根据你的实际情况调整）
    # base_audio_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/gf"
    # for i in os.listdir(base_audio_path):
    #     if i.endswith('.list'):
    #         lang = i.split('_')[1]
    #         src = f'{lang}.src'
    #         scp = f'{lang}.scp'
    #         audio = f"{lang}_wav"
    #         process_audio_list(os.path.join(base_audio_path, i), os.path.join(base_audio_path, src), os.path.join(base_audio_path, scp), os.path.join(base_audio_path, audio))
    #         print(f"处理完成！")

    
    # print('开始转换SOTA数据集...')                
    # sota_data_convert_scp_src(os.path.join(TEST_DATA_DIR_Sota1, 'SOTA1_content.jsonl'),1)
    # print('转换完成！')
    # process_audio_list(input_file, src_output_file, scp_output_file, base_path)
