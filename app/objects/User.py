class User:
    """
    用户类，管理单一用户的数据
    """
    def __init__(self, telegram_user_name: str = None, gender: int = None, user_id: str = None):
        # 用户基本信息（中文注释：user_id 改为字符串，存储微信 openid 或其他平台的字符串主键）
        self.user_id = user_id
        self.telegram_user_name = telegram_user_name
        self.gender = gender
        self.age = None
        self.target_gender = None
        self.user_personality_summary = None
        self.match_ids = []  # type: list[int] 匹配ID仍为数字
        self.blocked_user_ids = []  # type: list[str] 被屏蔽的用户ID（字符串）
        
        # 论坛相关字段（新增）
        self.post_ids = []           # type: list[int] - 用户发布的帖子ID列表
        self.liked_post_ids = []     # type: list[int] - 用户点赞的帖子ID列表（帖子ID为数字）

    def edit_data(self, telegram_user_name=None, gender=None, age=None, target_gender=None, user_personality_summary=None):
        """编辑用户数据"""
        if telegram_user_name is not None:
            self.telegram_user_name = telegram_user_name
        if gender is not None:
            self.gender = gender
        if age is not None:
            self.age = age
        if target_gender is not None:
            self.target_gender = target_gender
        if user_personality_summary is not None:
            self.user_personality_summary = user_personality_summary

    def get_user_id(self):
        return self.user_id

    def block_user(self, blocked_user_id: str):
        if blocked_user_id not in self.blocked_user_ids:
            self.blocked_user_ids.append(blocked_user_id)

    def like_match(self, match_id):
        if match_id not in self.match_ids:
            self.match_ids.append(match_id)
            
    # 论坛相关方法（新增）
    def add_post(self, post_id: int):
        """添加用户发布的帖子ID"""
        if post_id not in self.post_ids:
            self.post_ids.append(post_id)
            
    def remove_post(self, post_id: int):
        """移除用户发布的帖子ID"""
        if post_id in self.post_ids:
            self.post_ids.remove(post_id)
            
    def add_liked_post(self, post_id: int):
        """添加用户点赞的帖子ID"""
        if post_id not in self.liked_post_ids:
            self.liked_post_ids.append(post_id)
            
    def remove_liked_post(self, post_id: int):
        """移除用户点赞的帖子ID"""
        if post_id in self.liked_post_ids:
            self.liked_post_ids.remove(post_id)