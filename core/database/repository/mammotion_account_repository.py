from typing import Optional

from core.database.entity.aliyun_account import AliyunAccount
from core.database.entity.mammotion_account import MammotionAccount
from core.database.repository.base_repository import BaseRepository

class MammotionAccountRepository(BaseRepository[MammotionAccount]):
    def __init__(self):
        super().__init__(MammotionAccount)
        self.create_table()

    def get_aliyun_account(self, mammotion_account_id: str) -> Optional[AliyunAccount]:
        query = f"SELECT * FROM aliyun_account WHERE mammotion_account_id = '?'"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (mammotion_account_id,))
            row = cursor.fetchone()
            
            if row:
                return AliyunAccount(*row)
            return None
