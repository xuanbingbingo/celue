# 强制同步概念数据到本地

# sync_concepts.py
from utils.data_tools import update_concept_cache

if __name__ == "__main__":
    # 这一步会联网，耗时较久，但一天只需跑一次
    update_concept_cache()