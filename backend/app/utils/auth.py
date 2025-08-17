import bcrypt
import re
import logging
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class PasswordManager:
    """密码管理工具类"""

    # 默认密码策略配置
    DEFAULT_CONFIG = {
        "min_length": 8,
        "max_length": 128,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digits": True,
        "require_special_chars": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        "bcrypt_rounds": 12,  # bcrypt工作因子
    }

    def __init__(self, config: Optional[Dict] = None):
        """初始化密码管理器"""
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

    def hash_password(self, password: str) -> str:
        """对密码进行哈希加密"""
        try:
            # 验证密码强度
            validation_result = self.validate_password_strength(password)
            if not validation_result["is_valid"]:
                raise ValueError(
                    f"Password validation failed: {', '.join(validation_result['errors'])}"
                )

            # 生成盐值并加密
            salt = bcrypt.gensalt(rounds=self.config["bcrypt_rounds"])
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

            logger.info("Password hashed successfully")
            return hashed.decode("utf-8")

        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}")
            raise

    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码是否正确"""
        try:
            if not password or not hashed:
                return False

            result = bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

            if result:
                logger.info("Password verification successful")
            else:
                logger.warning("Password verification failed")

            return result

        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False

    def validate_password_strength(self, password: str) -> Dict:
        """验证密码强度"""
        errors = []

        # 检查密码长度
        if len(password) < self.config["min_length"]:
            errors.append(
                f"Password must be at least {self.config['min_length']} characters long"
            )

        if len(password) > self.config["max_length"]:
            errors.append(
                f"Password must not exceed {self.config['max_length']} characters"
            )

        # 检查大写字母
        if self.config["require_uppercase"] and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        # 检查小写字母
        if self.config["require_lowercase"] and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        # 检查数字
        if self.config["require_digits"] and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        # 检查特殊字符
        if self.config["require_special_chars"]:
            special_chars_pattern = f"[{re.escape(self.config['special_chars'])}]"
            if not re.search(special_chars_pattern, password):
                errors.append(
                    f"Password must contain at least one special character from: {self.config['special_chars']}"
                )

        # 检查常见弱密码模式
        weak_patterns = [
            (r"(.)\1{2,}", "Password should not contain repeated characters"),
            (
                r"123456|password|qwerty|admin",
                "Password should not contain common weak patterns",
            ),
            (r"^[0-9]+$", "Password should not be all numbers"),
            (r"^[a-zA-Z]+$", "Password should not be all letters"),
        ]

        for pattern, message in weak_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append(message)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength_score": self._calculate_strength_score(password),
        }

    def _calculate_strength_score(self, password: str) -> int:
        """计算密码强度分数 (0-100)"""
        score = 0

        # 长度分数 (最多30分)
        length_score = min(30, len(password) * 2)
        score += length_score

        # 字符类型分数 (每种类型10分，最多40分)
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(f"[{re.escape(self.config['special_chars'])}]", password):
            score += 10

        # 复杂性分数 (最多30分)
        unique_chars = len(set(password))
        complexity_score = min(30, unique_chars * 2)
        score += complexity_score

        return min(100, score)

    def generate_password_requirements(self) -> Dict:
        """生成密码要求说明"""
        requirements = []

        requirements.append(
            f"Length: {self.config['min_length']}-{self.config['max_length']} characters"
        )

        if self.config["require_uppercase"]:
            requirements.append("At least one uppercase letter (A-Z)")

        if self.config["require_lowercase"]:
            requirements.append("At least one lowercase letter (a-z)")

        if self.config["require_digits"]:
            requirements.append("At least one digit (0-9)")

        if self.config["require_special_chars"]:
            requirements.append(
                f"At least one special character ({self.config['special_chars']})"
            )

        return {"requirements": requirements, "config": self.config}


# 创建全局密码管理器实例
password_manager = PasswordManager()


# 保持向后兼容的函数
def hash_password(password: str) -> str:
    """对密码进行哈希加密（向后兼容）"""
    return password_manager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """验证密码是否正确（向后兼容）"""
    return password_manager.verify_password(password, hashed)


def validate_password_strength(password: str) -> Dict:
    """验证密码强度（新功能）"""
    return password_manager.validate_password_strength(password)


def get_password_requirements() -> Dict:
    """获取密码要求（新功能）"""
    return password_manager.generate_password_requirements()
