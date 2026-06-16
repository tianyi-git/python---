/**
 * 工具集页面逻辑
 */
(function() {
    'use strict';

    if (!localStorage.getItem('token')) {
        window.location.href = '/auth/login';
        return;
    }

    // ===== 天气查询 =====
    document.getElementById('weatherBtn').addEventListener('click', function() {
        var city = document.getElementById('weatherCity').value.trim();
        if (!city) { showToast('请输入城市名称', 'info'); return; }

        var btn = this;
        btn.disabled = true;
        btn.textContent = '查询中...';

        API.post('/tools/api/tools/weather', { city: city }).then(function(res) {
            var d = res.data;
            var iconUrl = 'https://openweathermap.org/img/wn/' + d.weather_icon + '@2x.png';
            document.getElementById('weatherResult').innerHTML =
                '<div class="weather-card">' +
                '<div style="display:flex;align-items:center;gap:12px;">' +
                '<img src="' + iconUrl + '" alt="" style="width:64px;">' +
                '<div>' +
                '<strong style="font-size:28px;">' + d.temperature + '°C</strong>' +
                '<p style="margin:0;">' + d.weather + '</p>' +
                '</div></div>' +
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;font-size:13px;">' +
                '<span>📍 ' + d.city + ', ' + d.country + '</span>' +
                '<span>💧 湿度: ' + d.humidity + '%</span>' +
                '<span>🌡️ 体感: ' + d.feels_like + '°C</span>' +
                '<span>💨 风速: ' + d.wind_speed + ' m/s</span>' +
                '<span>📊 气压: ' + d.pressure + ' hPa</span>' +
                '<span>👁️ 能见度: ' + d.visibility + ' m</span>' +
                '</div></div>';
        }).catch(function(err) {
            document.getElementById('weatherResult').innerHTML =
                '<p class="text-error">' + err.message + '</p>';
        }).finally(function() {
            btn.disabled = false;
            btn.textContent = '查询天气';
        });
    });

    // ===== 计算器 =====
    document.getElementById('calcBtn').addEventListener('click', function() {
        var expr = document.getElementById('calcExpr').value.trim();
        if (!expr) { showToast('请输入表达式', 'info'); return; }

        var btn = this;
        btn.disabled = true;

        API.post('/tools/api/tools/calculator', { expression: expr }).then(function(res) {
            document.getElementById('calcResult').innerHTML =
                '<div class="calc-display">' +
                '<div style="color:var(--color-text-muted);">' +
                escapeHtml(res.data.expression) + '</div>' +
                '<div style="font-size:28px;font-weight:700;color:var(--color-primary);">' +
                '= ' + res.data.result + '</div></div>';
        }).catch(function(err) {
            document.getElementById('calcResult').innerHTML =
                '<p class="text-error">' + err.message + '</p>';
        }).finally(function() {
            btn.disabled = false;
        });
    });

    // ===== 文本处理 =====
    document.querySelectorAll('.tool-btn-group .btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var text = document.getElementById('textInput').value;
            if (!text) { showToast('请先输入文本', 'info'); return; }

            var action = this.dataset.action;
            API.post('/tools/api/tools/text', { action: action, text: text }).then(function(res) {
                var html = '<div class="text-result-box">';
                if (action === 'count') {
                    html += '<p>📏 字符数: <strong>' + res.data.chars + '</strong></p>';
                    html += '<p>📝 不含空格: <strong>' + res.data.chars_no_space + '</strong></p>';
                    html += '<p>📄 单词数: <strong>' + res.data.words + '</strong></p>';
                    html += '<p>↩️ 行数: <strong>' + res.data.lines + '</strong></p>';
                } else {
                    html += '<p><strong>结果:</strong></p>';
                    html += '<pre>' + escapeHtml(res.data.result) + '</pre>';
                }
                html += '</div>';
                document.getElementById('textResult').innerHTML = html;
            }).catch(function(err) {
                document.getElementById('textResult').innerHTML =
                    '<p class="text-error">' + err.message + '</p>';
            });
        });
    });

    // ===== JSON 格式化 =====
    document.getElementById('jsonBtn').addEventListener('click', function() {
        var jsonStr = document.getElementById('jsonInput').value.trim();
        if (!jsonStr) { showToast('请输入 JSON 字符串', 'info'); return; }

        var btn = this;
        btn.disabled = true;

        API.post('/tools/api/tools/json', { json_str: jsonStr }).then(function(res) {
            document.getElementById('jsonResult').innerHTML =
                '<div class="text-result-box">' +
                '<p style="color:var(--color-success);">✅ JSON 格式正确</p>' +
                '<pre style="background:var(--color-surface-alt);padding:12px;border-radius:8px;overflow-x:auto;font-size:13px;">' +
                escapeHtml(res.data.formatted) + '</pre></div>';
        }).catch(function(err) {
            document.getElementById('jsonResult').innerHTML =
                '<p class="text-error">❌ ' + err.message + '</p>';
        }).finally(function() {
            btn.disabled = false;
        });
    });

    // ===== 工具函数 =====
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    function showToast(msg, type) {
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(function() { toast.remove(); }, 300);
        }, 2500);
    }
})();
