"""密码管理工具模块

提供密码哈希、验证等功能
"""

import bcrypt


class PasswordManager:
    """密码管理器

    使用bcrypt进行密码哈希和验证
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """对密码进行哈希加密

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        if not password:
            raise ValueError("密码不能为空")

        # 生成盐值并进行哈希
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """验证密码是否正确

        Args:
            password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            bool: 密码是否匹配
        """
        if not password or not hashed_password:
            return False

        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_password_strong(password: str) -> bool:
        """检查密码强度

        Args:
            password: 密码

        Returns:
            bool: 密码是否足够强
        """
        if not password or len(password) < 8:
            return False

        # 检查是否包含大小写字母、数字
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        return has_upper and has_lower and has_digit


# 创建全局实例
password_manager = PasswordManager()

# 导出函数
hash_password = password_manager.hash_password
verify_password = password_manager.verify_password
is_password_strong = password_manager.is_password_strong
