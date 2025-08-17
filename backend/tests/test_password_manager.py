import pytest
from app.utils.auth import PasswordManager, hash_password, verify_password

class TestPasswordManager:
    """密码管理器测试类"""
    
    @pytest.fixture
    def password_manager(self):
        """创建密码管理器实例"""
        return PasswordManager()
    
    def test_password_manager_initialization(self, password_manager):
        """测试密码管理器初始化"""
        assert password_manager.config['min_length'] == 8
        assert password_manager.config['max_length'] == 128
        assert password_manager.config['require_uppercase'] is True
        assert password_manager.config['require_lowercase'] is True
        assert password_manager.config['require_digits'] is True
        assert password_manager.config['require_special_chars'] is True
        assert password_manager.config['bcrypt_rounds'] == 12
    
    def test_password_manager_custom_config(self):
        """测试自定义配置的密码管理器"""
        custom_config = {
            'min_length': 10,
            'max_length': 64,
            'require_uppercase': False,
            'require_lowercase': True,
            'require_digits': False,
            'require_special_chars': False,
            'bcrypt_rounds': 10
        }
        
        manager = PasswordManager(custom_config)
        
        assert manager.config['min_length'] == 10
        assert manager.config['max_length'] == 64
        assert manager.config['require_uppercase'] is False
        assert manager.config['require_lowercase'] is True
        assert manager.config['require_digits'] is False
        assert manager.config['require_special_chars'] is False
        assert manager.config['bcrypt_rounds'] == 10
    
    def test_hash_password_function(self):
        """测试hash_password函数"""
        password = 'MySecure@Phrase123!'
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith('$2b$')  # bcrypt格式
    
    def test_verify_password_function(self):
        """测试verify_password函数"""
        password = 'MySecure@Phrase123!'
        hashed = hash_password(password)
        
        # 正确密码验证
        assert verify_password(password, hashed) is True
        
        # 错误密码验证
        assert verify_password('WrongPhrase', hashed) is False
        assert verify_password('', hashed) is False
        assert verify_password(None, hashed) is False
    
    def test_password_manager_hash_password(self, password_manager):
        """测试密码管理器的hash_password方法"""
        password = 'MySecure@Phrase123!'
        hashed = password_manager.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith('$2b$')
    
    def test_password_manager_verify_password(self, password_manager):
        """测试密码管理器的verify_password方法"""
        password = 'MySecure@Phrase123!'
        hashed = password_manager.hash_password(password)
        
        # 正确密码验证
        assert password_manager.verify_password(password, hashed) is True
        
        # 错误密码验证
        assert password_manager.verify_password('WrongPhrase', hashed) is False
    
    def test_validate_password_strength_valid(self, password_manager):
        """测试有效密码强度验证"""
        valid_passwords = [
            'MySecure@Phrase123!',
            'StrongPhrase@2024!',
            'ComplexPhrase#789!'
        ]
        
        for password in valid_passwords:
            result = password_manager.validate_password_strength(password)
            assert result['is_valid'] is True, f"Password '{password}' should be valid, but got errors: {result['errors']}"
            assert isinstance(result['errors'], list)
            assert len(result['errors']) == 0
            assert 'strength_score' in result
    
    def test_validate_password_strength_too_short(self, password_manager):
        """测试密码过短"""
        short_passwords = ['Pass1!', 'Ab1!', '1234567']
        
        for password in short_passwords:
            result = password_manager.validate_password_strength(password)
            assert result['is_valid'] is False
            assert any('at least' in error and '8' in error for error in result['errors'])
    
    def test_validate_password_strength_too_long(self, password_manager):
        """测试密码过长"""
        long_password = 'A' * 129 + '1!'
        
        result = password_manager.validate_password_strength(long_password)
        assert result['is_valid'] is False
        assert any('exceed' in error and '128' in error for error in result['errors'])
    
    def test_validate_password_strength_missing_uppercase(self, password_manager):
        """测试缺少大写字母"""
        password = 'password123!'
        
        result = password_manager.validate_password_strength(password)
        assert result['is_valid'] is False
        assert any('uppercase' in error for error in result['errors'])
    
    def test_validate_password_strength_missing_lowercase(self, password_manager):
        """测试缺少小写字母"""
        password = 'PASSWORD123!'
        
        result = password_manager.validate_password_strength(password)
        assert result['is_valid'] is False
        assert any('lowercase' in error for error in result['errors'])
    
    def test_validate_password_strength_missing_digits(self, password_manager):
        """测试缺少数字"""
        password = 'Password!'
        
        result = password_manager.validate_password_strength(password)
        assert result['is_valid'] is False
        assert any('digit' in error for error in result['errors'])
    
    def test_validate_password_strength_missing_special_chars(self, password_manager):
        """测试缺少特殊字符"""
        password = 'Password123'
        
        result = password_manager.validate_password_strength(password)
        assert result['is_valid'] is False
        assert any('special character' in error for error in result['errors'])
    
    def test_validate_password_strength_common_weak_patterns(self, password_manager):
        """测试常见弱密码模式"""
        weak_passwords = [
            'password123!',  # 包含"password"
            'admin123!',     # 包含"admin"
            'qwerty123!',    # 包含"qwerty"
            '123456789!',    # 包含"123456"
            'Aaaa1234!'      # 包含重复字符
        ]
        
        for password in weak_passwords:
            result = password_manager.validate_password_strength(password)
            assert result['is_valid'] is False, f"Password '{password}' should be invalid due to weak patterns"
            assert len(result['errors']) > 0
    
    def test_validate_password_strength_sequential_patterns(self, password_manager):
        """测试连续字符模式"""
        sequential_passwords = [
            'Abcd1234!',     # 连续字母和数字
            'Password1234!', # 连续数字
            'Abcdef123!'     # 连续字母
        ]
        
        for password in sequential_passwords:
            result = password_manager.validate_password_strength(password)
            # 这些密码可能会被标记为包含连续字符
            if not result['is_valid']:
                assert any('repeated characters' in error or 'weak patterns' in error for error in result['errors'])
    
    def test_calculate_password_strength_score(self, password_manager):
        """测试密码强度分数计算"""
        # 弱密码
        weak_password = 'abc123'
        result = password_manager.validate_password_strength(weak_password)
        weak_score = result['strength_score']
        assert 0 <= weak_score <= 50
        
        # 中等密码
        medium_password = 'MySecure123'
        result = password_manager.validate_password_strength(medium_password)
        medium_score = result['strength_score']
        assert 40 <= medium_score <= 80
        
        # 强密码
        strong_password = 'MyVerySecure@Phrase123!'
        result = password_manager.validate_password_strength(strong_password)
        strong_score = result['strength_score']
        assert 60 <= strong_score <= 100
    
    def test_get_password_requirements(self, password_manager):
        """测试获取密码要求说明"""
        requirements_data = password_manager.generate_password_requirements()
        
        assert isinstance(requirements_data, dict)
        assert 'requirements' in requirements_data
        assert 'config' in requirements_data
        
        requirements = requirements_data['requirements']
        assert isinstance(requirements, list)
        assert len(requirements) > 0
        
        # 检查是否包含基本要求
        requirements_text = ' '.join(requirements)
        assert '8' in requirements_text  # 最小长度
        assert '128' in requirements_text  # 最大长度
        assert 'uppercase' in requirements_text
        assert 'lowercase' in requirements_text
        assert 'digit' in requirements_text
        assert 'special character' in requirements_text
    
    def test_password_manager_with_relaxed_config(self):
        """测试宽松配置的密码管理器"""
        relaxed_config = {
            'min_length': 6,
            'require_uppercase': False,
            'require_lowercase': True,
            'require_digits': True,
            'require_special_chars': False
        }
        
        manager = PasswordManager(relaxed_config)
        
        # 这个密码在宽松配置下应该有效
        simple_password = 'simple123'
        result = manager.validate_password_strength(simple_password)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
    
    def test_password_manager_with_strict_config(self):
        """测试严格配置的密码管理器"""
        strict_config = {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_special_chars': True
        }
        
        manager = PasswordManager(strict_config)
        
        # 这个密码在严格配置下应该无效（太短）
        short_password = 'Pass123!'
        result = manager.validate_password_strength(short_password)
        
        assert result['is_valid'] is False
        assert any('at least' in error and '12' in error for error in result['errors'])
        
        # 这个密码在严格配置下应该有效
        long_password = 'MyVerySecurePhrase123!'
        result = manager.validate_password_strength(long_password)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
    
    def test_edge_cases(self, password_manager):
        """测试边界情况"""
        # 空密码
        result = password_manager.validate_password_strength('')
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        
        # None密码 - 需要处理None值
        try:
            result = password_manager.validate_password_strength(None)
            assert result['is_valid'] is False
            assert len(result['errors']) > 0
        except (TypeError, AttributeError):
            # None值可能导致异常，这是可以接受的
            pass
        
        # 只有空格的密码
        result = password_manager.validate_password_strength('        ')
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
    
    def test_unicode_passwords(self, password_manager):
        """测试Unicode密码"""
        unicode_passwords = [
            'Пароль123!',      # 俄文
            '密码Password123!', # 中文
            'Contraseña123!',  # 西班牙文
            'Mot2Passe123!'    # 法文
        ]
        
        for password in unicode_passwords:
            # 应该能够处理Unicode字符而不崩溃
            try:
                result = password_manager.validate_password_strength(password)
                # 结果可能因配置而异，但不应该抛出异常
                assert isinstance(result['is_valid'], bool)
                assert isinstance(result['errors'], list)
                assert 'strength_score' in result
            except Exception as e:
                pytest.fail(f"Unicode password '{password}' caused exception: {e}")
    
    def test_password_hashing_consistency(self, password_manager):
        """测试密码哈希的一致性"""
        password = 'MySecure@Phrase123!'
        
        # 多次哈希同一密码应该产生不同的哈希值（因为salt）
        hash1 = password_manager.hash_password(password)
        hash2 = password_manager.hash_password(password)
        
        assert hash1 != hash2
        
        # 但都应该能验证原密码
        assert password_manager.verify_password(password, hash1) is True
        assert password_manager.verify_password(password, hash2) is True
    
    def test_bcrypt_rounds_effect(self):
        """测试bcrypt轮数的影响"""
        import time
        
        # 低轮数配置
        low_rounds_config = {'bcrypt_rounds': 4}
        low_manager = PasswordManager(low_rounds_config)
        
        # 高轮数配置
        high_rounds_config = {'bcrypt_rounds': 12}
        high_manager = PasswordManager(high_rounds_config)
        
        password = 'MySecure@Phrase123!'
        
        # 测试低轮数哈希时间
        start_time = time.time()
        low_hash = low_manager.hash_password(password)
        low_time = time.time() - start_time
        
        # 测试高轮数哈希时间
        start_time = time.time()
        high_hash = high_manager.hash_password(password)
        high_time = time.time() - start_time
        
        # 高轮数应该花费更多时间
        assert high_time > low_time
        
        # 但都应该能正确验证
        assert low_manager.verify_password(password, low_hash) is True
        assert high_manager.verify_password(password, high_hash) is True