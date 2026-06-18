/**
 * 数据分析页面逻辑
 */
(function() {
    'use strict';

    // ===== 状态 =====
    var state = {
        fileId: null,
        savedName: null,
        filename: null,
        columns: [],
        numericColumns: [],
        currentTab: 'preview',
    };

    // ===== DOM =====
    var $ = function(id) { return document.getElementById(id); };

    var $fileInput = $('fileInput');
    var $uploadBtn = $('uploadBtn');
    var $chartPanel = $('chartPanel');
    var $queryPanel = $('queryPanel');
    var $infoPanel = $('infoPanel');
    var $dataTabs = $('dataTabs');
    var $emptyUpload = $('emptyUpload');
    var $previewTable = $('previewTable');
    var $generateChartBtn = $('generateChartBtn');
    var $queryBtn = $('queryBtn');
    var $correlationBtn = $('correlationBtn');

    // ===== 初始化 =====
    function init() {
        if (!localStorage.getItem('token')) {
            window.location.href = '/auth/login';
            return;
        }

        $uploadBtn.addEventListener('click', function() { $fileInput.click(); });
        $fileInput.addEventListener('change', handleFileUpload);
        $generateChartBtn.addEventListener('click', generateChart);
        $queryBtn.addEventListener('click', executeQuery);
        $correlationBtn.addEventListener('click', showCorrelation);

        // 标签页切换
        document.querySelectorAll('.data-tab').forEach(function(tab) {
            tab.addEventListener('click', function() {
                switchTab(this.dataset.tab);
            });
        });
    }

    // ===== 标签页 =====
    function switchTab(name) {
        state.currentTab = name;
        document.querySelectorAll('.data-tab').forEach(function(t) {
            t.classList.toggle('active', t.dataset.tab === name);
        });
        document.querySelectorAll('.tab-content').forEach(function(c) {
            c.classList.toggle('active', c.id === 'tab-' + name);
        });
    }

    // ===== 上传 =====
    function handleFileUpload() {
        var file = $fileInput.files[0];
        if (!file) return;

        var formData = new FormData();
        formData.append('file', file);

        $uploadBtn.disabled = true;
        $uploadBtn.textContent = '解析中...';

        fetch('/api/data/upload', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + API.getToken() },
            body: formData,
        }).then(function(resp) {
            if (resp.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/auth/login';
                return Promise.reject(new Error('未登录'));
            }
            return resp.json();
        })
          .then(function(res) {
              if (res.code === 200) {
                  state.fileId = res.data.file_id;
                  state.savedName = res.data.saved_name;
                  state.filename = res.data.filename;
                  state.columns = res.data.info.columns || [];
                  state.numericColumns = Object.entries(res.data.info.dtypes || {})
                      .filter(function(e) { return e[1].includes('int') || e[1].includes('float'); })
                      .map(function(e) { return e[0]; });

                  renderAll(res.data);
                  showToast('文件解析成功！', 'success');
              } else {
                  showToast(res.message, 'error');
              }
          }).catch(function(err) {
              showToast('上传失败: ' + err.message, 'error');
          }).finally(function() {
              $uploadBtn.disabled = false;
              $uploadBtn.textContent = '选择文件并上传';
              $fileInput.value = '';
          });
    }

    function renderAll(data) {
        // 显示面板
        $chartPanel.style.display = 'block';
        $queryPanel.style.display = 'block';
        $infoPanel.style.display = 'block';
        $dataTabs.style.display = 'flex';
        $emptyUpload.style.display = 'none';

        // 数据概览
        var info = data.info;
        $('fileInfo').innerHTML =
            '<p><strong>文件:</strong> ' + escapeHtml(state.filename) + '</p>' +
            '<p><strong>行数:</strong> ' + info.shape[0] + ' &times; <strong>列数:</strong> ' + info.shape[1] + '</p>' +
            '<p><strong>缺失值:</strong> ' + info.missing_total + '</p>' +
            '<p><strong>列名:</strong> ' + info.columns.map(escapeHtml).join(', ') + '</p>';

        // 数据预览表格
        renderTable(data.preview || [], info.columns);

        // 统计分析
        renderStats(data.stats, info.columns);

        // 切换到预览
        switchTab('preview');
    }

    function renderTable(rows, columns) {
        if (!rows.length) {
            $previewTable.innerHTML = '<p class="empty-hint">暂无数据</p>';
            return;
        }

        var html = '<table class="data-table"><thead><tr>';
        columns.forEach(function(col) {
            html += '<th>' + escapeHtml(col) + '</th>';
        });
        html += '</tr></thead><tbody>';

        rows.forEach(function(row) {
            html += '<tr>';
            columns.forEach(function(col) {
                html += '<td>' + escapeHtml(String(row[col] || '')) + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';

        $previewTable.style.display = 'block';
        $previewTable.innerHTML = html;
    }

    function renderStats(stats, columns) {
        if (stats.message) {
            $('statsContent').innerHTML = '<p>' + stats.message + '</p>';
            return;
        }

        var s = stats.stats;
        var keys = ['count', 'mean', 'std', 'min', 'q25', 'median', 'q75', 'max'];
        var labels = {
            count: '计数', mean: '均值', std: '标准差',
            min: '最小值', max: '最大值', median: '中位数',
            q25: '25%分位', q75: '75%分位',
        };

        var html = '<table class="data-table"><thead><tr><th>指标</th>';
        Object.keys(s.count || {}).forEach(function(col) {
            html += '<th>' + escapeHtml(col) + '</th>';
        });
        html += '</tr></thead><tbody>';

        keys.forEach(function(key) {
            html += '<tr><td><strong>' + (labels[key] || key) + '</strong></td>';
            Object.keys(s.count || {}).forEach(function(col) {
                var val = s[key] ? s[key][col] : '-';
                html += '<td>' + (val !== null && val !== undefined ? val : '-') + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';

        $('statsContent').innerHTML = html;
    }

    // ===== 图表 =====
    function generateChart() {
        var chartType = $('chartType').value;
        var xCol = $('xCol').value.trim() || null;
        var yCol = $('yCol').value.trim() || null;

        $generateChartBtn.disabled = true;
        $generateChartBtn.textContent = '生成中...';

        API.post('/api/data/chart', {
            saved_name: state.savedName,
            chart_type: chartType,
            x_col: xCol,
            y_col: yCol,
        }).then(function(res) {
            switchTab('chart');
            $('chartContent').innerHTML =
                '<img src="' + res.data.chart_url + '?t=' + Date.now() +
                '" alt="图表" style="max-width:100%;border-radius:8px;box-shadow:var(--shadow);">';
            showToast('图表生成成功', 'success');
        }).catch(function(err) {
            showToast(err.message, 'error');
        }).finally(function() {
            $generateChartBtn.disabled = false;
            $generateChartBtn.textContent = '生成图表';
        });
    }

    // ===== 查询 =====
    function executeQuery() {
        var query = $('queryStr').value.trim();
        if (!query) {
            showToast('请输入查询条件', 'info');
            return;
        }

        API.post('/api/data/query', {
            saved_name: state.savedName,
            query: query,
        }).then(function(res) {
            switchTab('query');
            var html = '<p style="margin-bottom: 12px;">📊 查询返回 <strong>' +
                       res.data.count + '</strong> 条结果</p>';
            if (res.data.results.length > 0) {
                html += '<table class="data-table"><thead><tr>';
                Object.keys(res.data.results[0]).forEach(function(col) {
                    html += '<th>' + escapeHtml(col) + '</th>';
                });
                html += '</tr></thead><tbody>';
                res.data.results.forEach(function(row) {
                    html += '<tr>';
                    Object.values(row).forEach(function(val) {
                        html += '<td>' + escapeHtml(String(val)) + '</td>';
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
            }
            $('queryContent').innerHTML = html;
        }).catch(function(err) {
            showToast(err.message, 'error');
        });
    }

    function showCorrelation() {
        API.post('/api/data/correlation', {
            saved_name: state.savedName,
        }).then(function(res) {
            switchTab('query');
            if (res.data.message) {
                $('queryContent').innerHTML = '<p>' + res.data.message + '</p>';
                return;
            }

            var cols = res.data.columns;
            var data = res.data.data;
            var html = '<h4 style="margin-bottom: 12px;">📈 相关系数矩阵</h4>';
            html += '<table class="data-table"><thead><tr><th></th>';
            cols.forEach(function(c) { html += '<th>' + escapeHtml(c) + '</th>'; });
            html += '</tr></thead><tbody>';
            cols.forEach(function(rowCol) {
                html += '<tr><td><strong>' + escapeHtml(rowCol) + '</strong></td>';
                cols.forEach(function(colCol) {
                    var val = data[rowCol] ? data[rowCol][colCol] : '-';
                    var color = '';
                    if (val !== null && val !== undefined && val !== '-') {
                        var intensity = Math.abs(val);
                        var hue = val >= 0 ? '67, 56, 211' : '239, 68, 68';
                        color = 'style="background: rgba(' + hue + ',' + intensity * 0.15 + ')"';
                    }
                    html += '<td ' + color + '>' +
                            (val !== null && val !== undefined ? val.toFixed(2) : '-') + '</td>';
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            $('queryContent').innerHTML = html;
        }).catch(function(err) {
            showToast(err.message, 'error');
        });
    }

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

    init();
})();
