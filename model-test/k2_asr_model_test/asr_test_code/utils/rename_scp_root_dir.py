import os
import glob

def replace_path_in_scp_files(root_dir):
    """
    替换.scp文件中的路径
    """
    # 定义要替换的旧路径和新路径
    old_path = "/nasStore/002-ASR-DataSets/099-TestData/Model_test_data"
    new_path = "/nasStore/002-ASR-DataSets/099-TestData/Model_test_data_k2"
    
    # 遍历根目录下的所有子目录
    for dataset_dir in os.listdir(root_dir):
        dataset_path = os.path.join(root_dir, dataset_dir)
        
        # 确保是目录
        if os.path.isdir(dataset_path):
            print(f"正在处理目录: {dataset_dir}")
            
            # 查找目录中所有.scp文件
            scp_files = glob.glob(os.path.join(dataset_path, "*.scp"))
            
            if not scp_files:
                print(f"  在 {dataset_dir} 中没有找到.scp文件")
                continue
            
            for scp_file in scp_files:
                print(f"  处理文件: {os.path.basename(scp_file)}")
                
                # 读取文件内容
                with open(scp_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 替换路径
                modified_lines = []
                for line in lines:
                    if old_path in line:
                        modified_line = line.replace(old_path, new_path)
                        modified_lines.append(modified_line)
                    else:
                        modified_lines.append(line)
                
                # 写回文件
                with open(scp_file, 'w', encoding='utf-8') as f:
                    f.writelines(modified_lines)
                
                print(f"    已处理 {len(lines)} 行，替换了 {len([l for l in lines if old_path in l])} 处路径")
    
    print("所有文件处理完成！")

def main():
    # 设置根目录
    root_dir = "/nasStore/002-ASR-DataSets/099-TestData/Model_test_data_k2"
    
    # 检查目录是否存在
    if not os.path.exists(root_dir):
        print(f"错误：目录不存在 - {root_dir}")
        return
    
    # 执行替换操作
    replace_path_in_scp_files(root_dir)

if __name__ == "__main__":
    main()