import os
import glob

def generate_scp_files(dataset_dir, output_dir=None):
    """
    生成按语种的.scp文件
    
    Args:
        dataset_dir: 数据集目录路径
        output_dir: 输出目录路径，如果为None则保存在dataset_dir下
    """
    if output_dir is None:
        output_dir = dataset_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有语种文件夹
    language_dirs = [d for d in os.listdir(dataset_dir) 
                    if os.path.isdir(os.path.join(dataset_dir, d))]
    
    print(f"找到 {len(language_dirs)} 个语种文件夹: {language_dirs}")
    
    for lang in language_dirs:
        lang_dir = os.path.join(dataset_dir, lang)
        
        # 查找该语种目录下的所有wav文件
        wav_files = glob.glob(os.path.join(lang_dir, "*.wav"))
        
        if not wav_files:
            print(f"警告: 在 {lang} 目录下未找到wav文件")
            continue
        
        # 按文件名排序
        wav_files.sort()
        
        # 生成.scp文件路径
        scp_file_path = os.path.join(output_dir, f"{lang}.scp")
        
        # 写入.scp文件，索引从1开始自动分配
        with open(scp_file_path, 'w', encoding='utf-8') as f:
            for index, wav_file in enumerate(wav_files, 0):
                # 索引从1开始自动分配，后面跟文件的绝对路径
                f.write(f"{index} {wav_file}\n")
        
        print(f"已生成 {lang}.scp, 包含 {len(wav_files)} 个文件")
    
    print("所有.scp文件生成完成！")

# 使用示例
if __name__ == "__main__":
    dataset_path = "/home/guojun/workspace/k2_asr_model_test/asr_test_code/test_data/outside_dataset/wenet_split/"
    generate_scp_files(dataset_path,dataset_path)