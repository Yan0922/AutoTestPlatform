import os.path


PRO_DPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_CODE_DIR = os.path.join(PRO_DPATH,'asr_test_code')
TEST_DATA_DIR = "/nasStore/002-ASR-DataSets/099-TestData/Model_test_data_k2"
MODEL_DIR = os.path.join(PRO_DPATH,'model')
# 30分钟的数据集
TEST_DATA_DIR_30 = os.path.join(TEST_DATA_DIR,'30_mins_dataset')
# sota1数据集
TEST_DATA_DIR_Sota1 = os.path.join(TEST_DATA_DIR,'SOTA-1-WAV')
# sota2数据集
TEST_DATA_DIR_Sota2 = os.path.join(TEST_DATA_DIR,'SOTA-2-WAV')
# sota3数据集
TEST_DATA_DIR_Sota3 = os.path.join(TEST_DATA_DIR,'SOTA-3-WAV')
# CV15数据集
TEST_DATA_DIR_CV15 = os.path.join(TEST_DATA_DIR,'CV15')
# gf数据集
TEST_DATA_DIR_gf = os.path.join(TEST_DATA_DIR,'gf')
# 场外测试数据集
TEST_DATA_DIR_outside_dataset = os.path.join(TEST_DATA_DIR,'outside_dataset')
# 测试结果存储
TEST_RESULT_DATA_DIR = os.path.join(TEST_CODE_DIR,'test_result')