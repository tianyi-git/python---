/**
 * API 请求封装
 * 自动注入 JWT Token，处理 401 自动跳转
 */
var API = (function() {
    'use strict';

    var BASE_URL = '';

    function getToken() {
        return localStorage.getItem('token');
    }

    function getHeaders() {
        var headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };
        var token = getToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        return headers;
    }

    function handleResponse(response) {
        if (response.status === 401) {
            // Token 过期或无效，跳转登录页
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/auth/login';
            return Promise.reject(new Error('未登录'));
        }
        return response.json().then(function(data) {
            if (response.ok) {
                return data;
            }
            throw new Error(data.message || '请求失败');
        });
    }

    function get(url) {
        return fetch(BASE_URL + url, {
            method: 'GET',
            headers: getHeaders(),
            credentials: 'same-origin',
        }).then(handleResponse);
    }

    function post(url, data) {
        return fetch(BASE_URL + url, {
            method: 'POST',
            headers: getHeaders(),
            credentials: 'same-origin',
            body: JSON.stringify(data),
        }).then(handleResponse);
    }

    function put(url, data) {
        return fetch(BASE_URL + url, {
            method: 'PUT',
            headers: getHeaders(),
            credentials: 'same-origin',
            body: JSON.stringify(data),
        }).then(handleResponse);
    }

    function del(url) {
        return fetch(BASE_URL + url, {
            method: 'DELETE',
            headers: getHeaders(),
            credentials: 'same-origin',
        }).then(handleResponse);
    }

    return {
        get: get,
        post: post,
        put: put,
        del: del,
        getToken: getToken,
    };
})();
