async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            // 确保正确保存 token
            localStorage.setItem('token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            
            // 获取用户信息
            const userResponse = await fetch('/api/users/me/', {
                headers: {
                    'Authorization': `Bearer ${data.access}`
                }
            });
            const userData = await userResponse.json();
            localStorage.setItem('user', JSON.stringify(userData));
            
            window.location.href = '/';
        } else {
            alert(data.detail || '登录失败');
        }
    } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败，请重试');
    }
}