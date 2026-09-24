const API = {
    SEARCH: '/api/articles/search/',
    DOWNLOAD: '/api/articles/download/',
    CITE: '/api/articles/cite/',
    COLLECT: '/api/articles/collect/',
    EXPORT: '/api/articles/export/',
    REGISTER: '/api/users/', 
    LOGIN: '/api/users/login/'
};

function getRequestHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
    };
}

// 初始化登录注册按钮事件
document.addEventListener('DOMContentLoaded', () => {
    initAuthButtons();
});

function initAuthButtons() {
    const loginButton = document.getElementById('loginButton');
    const registerButton = document.getElementById('registerButton');

    if (loginButton) {
        loginButton.addEventListener('click', () => {
            showLoginModal();
        });
    }

    if (registerButton) {
        registerButton.addEventListener('click', () => {
            showRegisterModal();
        });
    }
}

function showLoginModal() {
    window.location.href = '/login';
}

function showRegisterModal() {
    window.location.href = '/register';
}

// 获取 CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
