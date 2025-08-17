#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据格式验证功能
"""

import uuid
import re
from typing import Union


def validate_uuid(uuid_string: Union[str, uuid.UUID]) -> bool:
    """验证UUID格式
    
    Args:
        uuid_string: 要验证的UUID字符串或UUID对象
        
    Returns:
        bool: UUID格式是否有效
    """
    try:
        uuid.UUID(str(uuid_string))
        return True
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """验证邮箱格式
    
    Args:
        email: 要验证的邮箱地址
        
    Returns:
        bool: 邮箱格式是否有效
    """
    if not email or not isinstance(email, str):
        return False
        
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """验证手机号格式
    
    Args:
        phone: 要验证的手机号
        
    Returns:
        bool: 手机号格式是否有效
    """
    if not phone or not isinstance(phone, str):
        return False
        
    # 支持中国大陆手机号格式
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None


def validate_password_format(password: str) -> bool:
    """验证密码基本格式
    
    Args:
        password: 要验证的密码
        
    Returns:
        bool: 密码格式是否有效
    """
    if not password or not isinstance(password, str):
        return False
        
    # 基本长度检查
    return len(password) >= 6


def validate_integer_range(value: Union[str, int], min_val: int = None, max_val: int = None) -> bool:
    """验证整数范围
    
    Args:
        value: 要验证的值
        min_val: 最小值（可选）
        max_val: 最大值（可选）
        
    Returns:
        bool: 值是否在有效范围内
    """
    try:
        int_value = int(value)
        
        if min_val is not None and int_value < min_val:
            return False
            
        if max_val is not None and int_value > max_val:
            return False
            
        return True
    except (ValueError, TypeError):
        return False