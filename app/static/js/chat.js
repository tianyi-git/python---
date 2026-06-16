/**
 * 对话 SPA 界面逻辑
 * 会话管理 + 消息收发 + 模型切换
 */
(function() {
    'use strict';

    // ============================================================
    // 全局状态
    // ============================================================
    var state = {
        currentSessionId: null,
        currentModel: 'claude',
        sessions: [],
        isLoading: false,
    };

    // ============================================================
    // DOM 元素
    // ============================================================
    var $sessionList = document.getElementById('sessionList');
    var $chatMessages = document.getElementById('chatMessages');
    var $messageInput = document.getElementById('messageInput');
    var $sendBtn = document.getElementById('sendBtn');
    var $newChatBtn = document.getElementById('newChatBtn');
    var $chatTitle = document.getElementById('chatTitle');
    var $modelSelect = document.getElementById('modelSelect');
    var $systemPrompt = document.getElementById('systemPrompt');
    var $saveSystemPrompt = document.getElementById('saveSystemPrompt');
    var $emptyState = document.getElementById('emptyState');
    var $modelList = document.getElementById('modelList');

    // ============================================================
    // 初始化
    // ============================================================
    function init() {
        if (!localStorage.getItem('token')) {
            window.location.href = '/auth/login';
            return;
        }
        loadSessions();
        loadModels();
        bindEvents();
    }

    function bindEvents() {
        $sendBtn.addEventListener('click', handleSend);
        $newChatBtn.addEventListener('click', createNewSession);
        $chatTitle.addEventListener('blur', saveTitle);
        $chatTitle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); $chatTitle.blur(); }
        });
        $modelSelect.addEventListener('change', onModelChange);
        $saveSystemPrompt.addEventListener('click', saveSystemPrompt);

        // Enter 发送, Shift+Enter 换行
        $messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        // 自动调整 textarea 高度
        $messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 160) + 'px';
        });

        // 输入框内容变化时切换发送按钮状态
        $messageInput.addEventListener('input', function() {
            $sendBtn.disabled = !this.value.trim() || state.isLoading;
        });
    }

    // ============================================================
    // 会话列表
    // ============================================================
    function loadSessions() {
        API.get('/api/chat/sessions').then(function(res) {
            state.sessions = res.data.sessions || [];
            renderSessionList();

            // 自动加载最近会话或显示空状态
            if (state.sessions.length > 0) {
                loadSession(state.sessions[0].id);
            } else {
                showEmptyState();
            }
        }).catch(function(err) {
            showToast('加载会话列表失败: ' + err.message, 'error');
        });
    }

    function renderSessionList() {
        $sessionList.innerHTML = '';

        state.sessions.forEach(function(session) {
            var item = document.createElement('div');
            item.className = 'session-item' + (session.id === state.currentSessionId ? ' active' : '');
            item.innerHTML =
                '<button class="session-item-delete" data-id="' + session.id + '">×</button>' +
                '<div class="session-item-title">' + escapeHtml(session.title) + '</div>' +
                '<div class="session-item-time">' + formatTime(session.updated_at) + '</div>';

            item.addEventListener('click', function(e) {
                if (e.target.classList.contains('session-item-delete')) return;
                loadSession(session.id);
            });

            var deleteBtn = item.querySelector('.session-item-delete');
            deleteBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                deleteSession(session.id);
            });

            $sessionList.appendChild(item);
        });
    }

    function createNewSession() {
        if (state.isLoading) return;

        API.post('/api/chat/sessions', {
            title: '新的对话',
            model_name: state.currentModel,
            system_prompt: $systemPrompt.value || null,
        }).then(function(res) {
            state.currentSessionId = res.data.session.id;
            $chatTitle.value = '新的对话';
            $chatMessages.innerHTML = '';
            showEmptyState();
            loadSessions();
            $messageInput.focus();
        }).catch(function(err) {
            showToast('创建会话失败: ' + err.message, 'error');
        });
    }

    function loadSession(sessionId) {
        state.currentSessionId = sessionId;
        API.get('/api/chat/sessions/' + sessionId).then(function(res) {
            var session = res.data.session;
            var messages = res.data.messages || [];

            $chatTitle.value = session.title;
            $systemPrompt.value = session.system_prompt || '';
            $modelSelect.value = session.model_name || 'claude';
            state.currentModel = session.model_name || 'claude';

            renderMessages(messages);
            renderSessionList();
            scrollToBottom();
        }).catch(function(err) {
            showToast('加载会话失败: ' + err.message, 'error');
        });
    }

    function deleteSession(sessionId) {
        if (!confirm('确定删除这个对话吗？')) return;

        API.del('/api/chat/sessions/' + sessionId).then(function() {
            if (state.currentSessionId === sessionId) {
                state.currentSessionId = null;
                $chatMessages.innerHTML = '';
                showEmptyState();
                $chatTitle.value = '新的对话';
            }
            loadSessions();
        }).catch(function(err) {
            showToast('删除失败: ' + err.message, 'error');
        });
    }

    function saveTitle() {
        var newTitle = $chatTitle.value.trim() || '新的对话';
        $chatTitle.value = newTitle;

        if (!state.currentSessionId) return;

        API.put('/api/chat/sessions/' + state.currentSessionId, {
            title: newTitle,
        }).then(function() {
            loadSessions(); // 刷新侧边栏
        }).catch(function() {
            /* 静默失败 */
        });
    }

    function saveSystemPrompt() {
        if (!state.currentSessionId) {
            showToast('请先创建或选择一个对话', 'info');
            return;
        }

        API.put('/api/chat/sessions/' + state.currentSessionId, {
            system_prompt: $systemPrompt.value,
        }).then(function() {
            showToast('提示词已保存', 'success');
        }).catch(function(err) {
            showToast('保存失败: ' + err.message, 'error');
        });
    }

    function onModelChange() {
        state.currentModel = $modelSelect.value;
        if (state.currentSessionId) {
            API.put('/api/chat/sessions/' + state.currentSessionId, {
                model_name: state.currentModel,
            }).catch(function() { /* 静默 */ });
        }
    }

    // ============================================================
    // 模型列表
    // ============================================================
    function loadModels() {
        API.get('/api/chat/models').then(function(res) {
            var models = res.data.models || [];
            $modelList.innerHTML = models.map(function(m) {
                var cls = 'model-option';
                if (m.id === state.currentModel) cls += ' active';
                if (!m.available) cls += ' unavailable';
                return '<div class="' + cls + '" data-model="' + m.id + '">' +
                    '<span>' + (m.available ? '🟢' : '🔴') + '</span>' +
                    '<span>' + escapeHtml(m.name) + '</span>' +
                    (m.hint ? '<small>' + escapeHtml(m.hint) + '</small>' : '') +
                '</div>';
            }).join('');

            // 绑定模型选择点击
            $modelList.querySelectorAll('.model-option.available').forEach(function(el) {
                el.addEventListener('click', function() {
                    state.currentModel = this.dataset.model;
                    $modelSelect.value = state.currentModel;
                    if (state.currentSessionId) {
                        API.put('/api/chat/sessions/' + state.currentSessionId, {
                            model_name: state.currentModel,
                        });
                    }
                    loadModels();
                });
            });

            // 更新 select 选项
            $modelSelect.innerHTML = models.map(function(m) {
                return '<option value="' + m.id + '"' +
                    (m.id === state.currentModel ? ' selected' : '') +
                    (m.available ? '' : ' disabled') + '>' +
                    m.name + (m.available ? '' : ' (不可用)') +
                '</option>';
            }).join('');
        }).catch(function() {
            /* 静默失败 — 使用默认模型 */
        });
    }

    // ============================================================
    // 消息收发
    // ============================================================
    function handleSend() {
        var message = $messageInput.value.trim();
        if (!message || state.isLoading) return;

        state.isLoading = true;
        $sendBtn.disabled = true;

        // 如果没有当前会话，先创建
        if (!state.currentSessionId) {
            var title = message.substring(0, 30) + (message.length > 30 ? '...' : '');
            API.post('/api/chat/sessions', {
                title: title,
                model_name: state.currentModel,
                system_prompt: $systemPrompt.value || null,
            }).then(function(res) {
                state.currentSessionId = res.data.session.id;
                $chatTitle.value = title;
                loadSessions();
                doSend(message);
            }).catch(function(err) {
                state.isLoading = false;
                $sendBtn.disabled = false;
                showToast('创建会话失败: ' + err.message, 'error');
            });
        } else {
            doSend(message);
        }
    }

    function doSend(message) {
        // 隐藏空状态
        hideEmptyState();

        // 显示用户消息
        appendMessage('user', message);
        $messageInput.value = '';
        $messageInput.style.height = 'auto';
        scrollToBottom();

        // 显示打字动画
        var typingEl = appendTyping();

        API.post('/api/chat/send', {
            session_id: state.currentSessionId,
            message: message,
            model: state.currentModel,
        }).then(function(res) {
            // 移除打字动画
            if (typingEl) typingEl.remove();

            // 显示 AI 回复
            appendMessage('assistant', res.data.reply, res.data.model);
            scrollToBottom();

            // 刷新会话列表（更新时间、标题等）
            loadSessions();
        }).catch(function(err) {
            if (typingEl) typingEl.remove();
            appendMessage('assistant', '❌ 错误: ' + err.message, 'system');
            scrollToBottom();
        }).finally(function() {
            state.isLoading = false;
            $sendBtn.disabled = false;
            $messageInput.focus();
        });
    }

    // ============================================================
    // UI 辅助
    // ============================================================
    function appendMessage(role, content, modelName) {
        var div = document.createElement('div');
        div.className = 'message ' + role;

        var bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // 简单 Markdown: 代码块
        var html = escapeHtml(content);
        html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, function(_, lang, code) {
            return '<pre><code>' + escapeHtml(code.trim()) + '</code></pre>';
        });
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        html = html.replace(/\n/g, '<br>');

        bubble.innerHTML = html;

        if (modelName && role === 'assistant') {
            var meta = document.createElement('div');
            meta.style.cssText = 'font-size:11px;color:var(--color-text-muted);margin-top:4px;';
            meta.textContent = '模型: ' + modelName;
            bubble.appendChild(meta);
        }

        div.appendChild(bubble);
        $chatMessages.appendChild(div);
    }

    function appendTyping() {
        var div = document.createElement('div');
        div.className = 'message assistant';
        div.id = 'typingIndicator';
        div.innerHTML = '<div class="message-bubble"><div class="typing-indicator">' +
            '<span></span><span></span><span></span></div></div>';
        $chatMessages.appendChild(div);
        scrollToBottom();
        return div;
    }

    function renderMessages(messages) {
        $chatMessages.innerHTML = '';
        if (!messages || messages.length === 0) {
            showEmptyState();
            return;
        }
        hideEmptyState();
        messages.forEach(function(msg) {
            appendMessage(msg.role, msg.content, msg.model_name);
        });
    }

    function showEmptyState() {
        $emptyState.style.display = 'flex';
    }

    function hideEmptyState() {
        $emptyState.style.display = 'none';
    }

    function scrollToBottom() {
        setTimeout(function() {
            $chatMessages.scrollTop = $chatMessages.scrollHeight;
        }, 50);
    }

    // ============================================================
    // 工具函数
    // ============================================================
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    function formatTime(isoStr) {
        if (!isoStr) return '';
        var d = new Date(isoStr);
        var now = new Date();
        var diff = now - d;
        if (diff < 60000) return '刚刚';
        if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前';
        if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前';
        return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }

    function showToast(message, type) {
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(function() { toast.remove(); }, 300);
        }, 2500);
    }

    // ============================================================
    // 启动
    // ============================================================
    init();
})();
