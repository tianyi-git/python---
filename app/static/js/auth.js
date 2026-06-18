/**
 * 认证表单处理
 * 登录 / 注册 页面共用
 */
(function() {
    'use strict';

    var form = document.querySelector('.auth-form');
    if (!form) return;

    var submitBtn = document.getElementById('submitBtn');
    var formError = document.getElementById('formError');

    // 判断是登录还是注册
    var isLogin = form.id === 'loginForm';

    function clearErrors() {
        var errors = document.querySelectorAll('.form-error');
        errors.forEach(function(el) { el.textContent = ''; });
        var inputs = document.querySelectorAll('.input-error');
        inputs.forEach(function(el) { el.classList.remove('input-error'); });
    }

    function showFieldError(fieldId, message) {
        var el = document.getElementById(fieldId + 'Error');
        if (el) el.textContent = message;
        var input = document.getElementById(fieldId);
        if (input) input.classList.add('input-error');
    }

    function setLoading(loading) {
        submitBtn.disabled = loading;
        submitBtn.textContent = loading ? '处理中...' : (isLogin ? '登 录' : '注 册');
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        clearErrors();
        setLoading(true);

        var username = document.getElementById('username').value.trim();
        var password = document.getElementById('password').value.trim();

        // 基本客户端校验
        if (!username) {
            showFieldError('username', '请输入用户名');
            setLoading(false);
            return;
        }
        if (!password) {
            showFieldError('password', '请输入密码');
            setLoading(false);
            return;
        }

        if (isLogin) {
            // ---- 登录 ----
            API.post('/api/auth/login', {
                username: username,
                password: password,
            }).then(function(res) {
                localStorage.setItem('token', res.data.token);
                localStorage.setItem('user', JSON.stringify(res.data.user));
                window.location.href = '/chat';
            }).catch(function(err) {
                formError.textContent = err.message;
                setLoading(false);
            });
        } else {
            // ---- 注册 ----
            var email = document.getElementById('email').value.trim();
            var confirmPassword = document.getElementById('confirmPassword').value.trim();

            if (!email) {
                showFieldError('email', '请输入邮箱');
                setLoading(false);
                return;
            }
            if (password.length < 6) {
                showFieldError('password', '密码至少6个字符');
                setLoading(false);
                return;
            }
            if (password !== confirmPassword) {
                showFieldError('confirmPassword', '两次密码输入不一致');
                setLoading(false);
                return;
            }

            API.post('/api/auth/register', {
                username: username,
                email: email,
                password: password,
            }).then(function(res) {
                localStorage.setItem('token', res.data.token);
                localStorage.setItem('user', JSON.stringify(res.data.user));
                window.location.href = '/chat';
            }).catch(function(err) {
                formError.textContent = err.message;
                setLoading(false);
            });
        }
    });
})();
