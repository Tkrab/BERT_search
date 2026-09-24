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

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    initializeEventListeners();
});


// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch('/api/users/', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const data = await response.json();
        renderUsers(data);
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

// 渲染用户列表
function renderUsers(users) {
    const userList = document.getElementById('userList');
    
    userList.innerHTML = users.map(user => `
        <tr>
            <td class="px-4 py-2">${user.username}</td>
            <td class="px-4 py-2">${user.email || ''}</td>
            <td class="px-4 py-2">
                <select onchange="updateUserVip(${user.id}, this.value)" class="border rounded px-2 py-1">
                    <option value="0" ${!user.is_vip ? 'selected' : ''}>普通用户</option>
                    <option value="1" ${user.is_vip ? 'selected' : ''}>VIP</option>
                </select>
            </td>
            <td class="px-4 py-2">
                <select onchange="updateUserRole(${user.id}, this.value)" class="border rounded px-2 py-1">
                    <option value="0" ${!user.is_staff ? 'selected' : ''}>普通用户</option>
                    <option value="1" ${user.is_staff ? 'selected' : ''}>管理员</option>
                </select>
            </td>
            <td class="px-4 py-2">
                <button onclick="editUser(${user.id})" class="text-blue-500 hover:text-blue-700 mr-2">编辑</button>
                <button onclick="deleteUser(${user.id})" class="text-red-500 hover:text-red-700">删除</button>
            </td>
        </tr>
    `).join('');
}

// 初始化事件监听器
function initializeEventListeners() {
    // 用户搜索
    document.getElementById('userSearch').addEventListener('input', (e) => {
        filterUsers(e.target.value);
    });
}

// 创建用户表单
function createUserForm(user = null) {
    return `
        <form ${user ? `data-user-id="${user.id}"` : ''} action="/api/users/${user?.id || ''}" method="post">
            <div class="mb-4">
                <label class="block text-gray-700 mb-2">用户名</label>
                <input type="text" name="username" value="${user?.username || ''}" class="w-full p-2 border rounded" required>
            </div>
            <div class="mb-4">
                <label class="block text-gray-700 mb-2">邮箱</label>
                <input type="email" name="email" value="${user?.email || ''}" class="w-full p-2 border rounded" required>
            </div>
            ${!user ? `
            <div class="mb-4">
                <label class="block text-gray-700 mb-2">密码</label>
                <input type="password" name="password" class="w-full p-2 border rounded" required>
            </div>
            ` : ''}
            <div class="flex justify-end">
                <button type="button" onclick="document.getElementById('modal').classList.add('hidden')" class="bg-gray-500 text-white px-4 py-2 rounded mr-2">取消</button>
                <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">保存</button>
            </div>
        </form>
    `;
}

function openModal(title, content) {
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalForm = document.getElementById('modalForm');

    modalTitle.textContent = title;
    modalForm.innerHTML = content;
    modal.classList.remove('hidden');

    const form = modalForm.querySelector('form');
    if (form) {
        // 移除表单的默认 action
        form.removeAttribute('action');
        
        form.addEventListener('submit', async (event) => {
            event.preventDefault();  // 确保阻止默认提交行为
            const formData = new FormData(form);
            const userId = form.getAttribute('data-user-id');
            
            const userData = {
                username: formData.get('username'),
                email: formData.get('email')
            };

            try {
                const url = `/api/users/${userId}/`;
                console.log('发送请求:', {url, userData});  // 添加日志
                
                const response = await fetch(url, {
                    method: 'PATCH',  // 改为 PATCH 方法
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(userData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || '操作失败');
                }

                modal.classList.add('hidden');
                loadUsers();
            } catch (error) {
                console.error('保存失败:', error);
                alert(error.message || '保存失败，请重试');
            }
        });
    }
}

// 编辑用户
async function editUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const user = await response.json();
        openModal('编辑用户', createUserForm(user));  // 使用 openModal
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

// 更新用户角色
async function updateUserRole(userId, isStaff) {
    try {
        const response = await fetch(`/api/users/${userId}/update_role/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ is_staff: isStaff === '1' })
        });
        
        if (!response.ok) {
            throw new Error('更新用户角色失败');
        }
        
        // 刷新用户列表
        loadUsers();
    } catch (error) {
        console.error('更新用户角色失败:', error);
        alert('更新用户角色失败，请重试');
    }
}

// 创建用户组表单
function createGroupForm(group = null) {
    return `
        <form>
            <div class="mb-4">
                <label class="block text-gray-700 mb-2">组名</label>
                <input type="text" name="name" value="${group?.name || ''}" class="w-full p-2 border rounded" required>
                <p class="text-sm text-gray-500 mt-1">提示：组名包含"管理员"的用户组成员将自动获得管理员权限</p>
            </div>
            <div class="flex justify-end">
                <button type="button" onclick="document.getElementById('modal').classList.add('hidden')" class="bg-gray-500 text-white px-4 py-2 rounded mr-2">取消</button>
                <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">保存</button>
            </div>
        </form>
    `;
}

// 添加处理用户组表单提交的函数
async function handleGroupSubmit(event, groupId) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const name = formData.get('name');

    try {
        const url = groupId ? `/api/groups/${groupId}/` : '/api/groups/';
        const method = groupId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ name: name })
        });

        if (!response.ok) {
            throw new Error('操作失败');
        }

        // 关闭模态框
        document.getElementById('modal').classList.add('hidden');
        // 刷新用户组列表
        loadGroups();
    } catch (error) {
        console.error('保存用户组失败:', error);
        alert('保存用户组失败，请重试');
    }
}

// 删除用户
async function deleteUser(userId) {
    if (!confirm('确定要删除这个用户吗？')) return;

    try {
        await fetch(`/api/users/${userId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        loadUsers();
    } catch (error) {
        console.error('删除用户失败:', error);
    }
}

// 编辑用户组
async function editGroup(groupId) {
    try {
        const response = await fetch(`/api/groups/${groupId}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const group = await response.json();
        openModal('编辑用户组', createGroupForm(group));  // 将 showModal 改为 openModal
    } catch (error) {
        console.error('获取用户组信息失败:', error);
    }
}

// 删除用户组
async function deleteGroup(groupId) {
    if (!confirm('确定要删除这个用户组吗？')) return;

    try {
        await fetch(`/api/groups/${groupId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });
        loadGroups();
    } catch (error) {
        console.error('删除用户组失败:', error);
        alert('删除用户组失败，请重试');
    }
}

// 过滤用户列表
function filterUsers(query) {
    const rows = document.querySelectorAll('#userList tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
    });
}

// 过滤用户组列表
function filterGroups(query) {
    const rows = document.querySelectorAll('#groupList tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
    });
}
// 添加更新用户 VIP 状态的函数
async function updateUserVip(userId, isVip) {
    try {
        const response = await fetch(`/api/users/${userId}/toggle_vip/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ is_vip: isVip === '1' })
        });
        
        if (!response.ok) {
            throw new Error('更新用户 VIP 状态失败');
        }
        
        // 刷新用户列表
        loadUsers();
    } catch (error) {
        console.error('更新用户 VIP 状态失败:', error);
        alert('更新用户 VIP 状态失败，请重试');
    }
}