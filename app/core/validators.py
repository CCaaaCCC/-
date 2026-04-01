import re


def validate_password(password: str, strict: bool = False) -> bool:
    """
    验证密码强度
    宽松模式（默认）：至少 6 位
    严格模式（管理员/教师）：至少 8 位，包含大小写字母和数字
    """
    if strict:
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    return len(password) >= 6


def is_strict_password_role(role: str) -> bool:
    """管理员/教师使用严格密码策略。"""
    return role in ['admin', 'teacher']


def get_password_rule_text(strict: bool) -> str:
    return "至少 8 位，包含大小写字母和数字" if strict else "至少 6 位"


def validate_username(username: str) -> bool:
    """
    验证用户名格式
    要求：只能包含字母、数字、下划线，3-20 位
    """
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email:
        return True
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))
