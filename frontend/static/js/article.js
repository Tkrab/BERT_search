document.addEventListener('DOMContentLoaded', async () => {
    // 修改获取文章 ID 的方式
    const pathParts = window.location.pathname.split('/');
    const articleId = pathParts[pathParts.indexOf('article') + 1];
    
    try {
        // 获取文章数据
        const response = await fetch(`/api/articles/${articleId}/`);
        if (!response.ok) throw new Error('文章获取失败');
        const article = await response.json();
        
        // 设置文章 ID 到 DOM 元素
        document.querySelector('.article-info').dataset.articleId = articleId;
        
        // 更新页面内容
        document.getElementById('articleTitle').textContent = article.title;
        document.getElementById('articleAuthor').textContent = article.author;
        document.getElementById('articleSource').textContent = article.source;
        document.getElementById('articleDate').textContent = new Date(article.publication_date).toLocaleDateString();
        document.getElementById('articleAbstract').textContent = article.abstract;
        
        // 更新关键词
        if (article.keywords) {
            const keywordsContainer = document.getElementById('articleKeywords');
            article.keywords.forEach(keyword => {
                const span = document.createElement('span');
                span.className = 'keyword';
                span.textContent = keyword;
                keywordsContainer.appendChild(span);
            });
        }
        
        // 初始化其他功能
        initArticleActions();
        initRelationshipGraph();
        
    } catch (error) {
        console.error('获取文章详情失败:', error);
        alert('获取文章详情失败，请稍后重试');
    }
});

function initArticleActions() {
    const actionButtons = document.querySelectorAll('.action-button');
    actionButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const action = e.target.textContent.trim();
            const articleId = document.querySelector('[data-article-id]').dataset.articleId;
            
            switch(action) {
                case '下载全文':
                    await handleDownload(articleId);
                    break;
                case '导出引用':
                    await handleCite(articleId);
                    break;
                case '收藏文献':
                    await handleCollect(articleId);
                    break;
            }
        });
    });
}

// 添加处理函数
async function handleDownload(articleId) {
    try {
        const response = await fetch(`/api/articles/${articleId}/download/`);
        if (!response.ok) throw new Error('下载失败');
        
        // 获取文件名
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'article.pdf';
        
        // 创建 blob 并下载
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('下载文件失败:', error);
        alert('下载失败，请稍后重试');
    }
}

async function handleCite(articleId) {
    try {
        const response = await fetch(`/api/articles/${articleId}/cite/`);
        if (!response.ok) throw new Error('获取引用信息失败');
        const citation = await response.text();
        
        // 创建临时输入框复制内容
        const textarea = document.createElement('textarea');
        textarea.value = citation;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        alert('引用信息已复制到剪贴板');
    } catch (error) {
        console.error('获取引用信息失败:', error);
        alert('获取引用信息失败，请稍后重试');
    }
}

// 在文件开头添加
document.addEventListener('DOMContentLoaded', () => {
    const userSection = document.getElementById('userSection');
    const user = JSON.parse(localStorage.getItem('user'));

    if (user) {
        let html = `
            <div class="flex items-center space-x-4">
                <a href="/profile" class="text-white hover:text-gray-300">${user.username}</a>
        `;
        
        if (user.is_superuser || user.is_staff) {
            html += `<a href="/admin" class="text-white hover:text-gray-300">管理控制台</a>`;
        }

        html += `
                <a href="/" class="text-white hover:text-gray-300">首页</a>
            </div>
        `;
        
        userSection.innerHTML = html;
    } else {
        userSection.innerHTML = `
            <div class="flex items-center space-x-4">
                <button id="loginButton" class="text-white hover:text-gray-300">登录</button>
                <button id="registerButton" class="text-white hover:text-gray-300">注册</button>
                <a href="/" class="text-white hover:text-gray-300">首页</a>
            </div>
        `;
    }
});

// 修改 handleCollect 函数
async function handleCollect(articleId) {
    const user = JSON.parse(localStorage.getItem('user'));
    const token = localStorage.getItem('token');
    
    console.log('当前用户信息:', user);
    console.log('当前token:', token);
    
    if (!user || !token) {
        alert('请先登录');
        window.location.href = '/login';
        return;
    }

    try {
        console.log('发送收藏请求...');
        console.log('请求URL:', `/api/articles/${articleId}/collect/`);
        console.log('请求头:', {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-CSRFToken': getCookie('csrftoken')
        });

        const response = await fetch(`/api/articles/${articleId}/collect/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include'
        });
        
        console.log('收藏请求状态:', response.status);
        console.log('响应头:', Object.fromEntries(response.headers.entries()));
        
        const responseText = await response.text();
        console.log('原始响应内容:', responseText);
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('JSON解析失败:', e);
            throw new Error('服务器响应格式错误');
        }
        
        console.log('收藏响应数据:', data);
        
        if (!response.ok) {
            throw new Error(data.error || '收藏失败');
        }
        
        alert(data.message || '收藏成功');
    } catch (error) {
        console.error('收藏文献失败:', error);
        console.error('错误详情:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        alert(error.message || '收藏失败，请稍后重试');
    }
}

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

async function initRelationshipGraph() {
    const graphContainer = document.getElementById('relationshipGraph');
    if (!graphContainer) return;

    // 添加加载指示器
    graphContainer.innerHTML = `
        <div class="graph-loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">正在加载文献关系图谱...</p>
        </div>
    `;

    try {
    const articleId = document.querySelector('[data-article-id]').dataset.articleId;
    const response = await fetch(`/api/articles/${articleId}/graph/`);
    if (!response.ok) throw new Error('获取关系图谱数据失败');
    const data = await response.json();

    // 处理节点标签，存原始名字
    let counter = 1;
    data.nodes.forEach((node) => {
        node.label = { show: true };
        node.originalName = node.name; // 存原始名字

        if (node.id === articleId) {
            node.name = "本文献";
        } else {
            node.name = `文献${counter}`;
            counter++;
        }
    });

    console.log("最终节点数据:", data.nodes);

    // 清除加载指示器并创建图表容器
    const graphContainer = document.getElementById('graph-container');
    graphContainer.innerHTML = '<div id="echarts-container" style="width: 100%; height: 400px;"></div>';

    // 初始化 ECharts
    const chart = echarts.init(document.getElementById('echarts-container'));

    // 配置关系图
    const option = {
        title: {
            text: '文献关系图谱'
        },
        tooltip: {
            formatter: function (params) {
                return params.data.originalName || params.data.name; // 显示原始名字
            }
        },
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [{
            type: 'graph',
            layout: 'force',
            force: {
                repulsion: 100,
                edgeLength: 100
            },
            roam: true,
            label: {
                show: true
            },
            data: data.nodes,
            links: data.links,
            lineStyle: {
                opacity: 0.9,
                width: 2,
                curveness: 0
            }
        }]
    };

    chart.setOption(option);

    window.addEventListener('resize', () => {
        chart.resize();
    });

} catch (error) {
    console.error('初始化关系图谱失败:', error);
    const graphContainer = document.getElementById('graph-container');
    graphContainer.innerHTML = '<p class="error-message">加载关系图谱失败</p>';
}

}



