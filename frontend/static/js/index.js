document.addEventListener('DOMContentLoaded', () => {
    initSearchForm();
    initRecommendations();
});

function initSearchForm() {
    const searchForm = document.querySelector('#searchForm');
    if (!searchForm) return;
    
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const keyword = document.querySelector('#searchQuery').value;
        window.location.href = `/search?keyword=${encodeURIComponent(keyword)}`;
    });
}

async function initRecommendations() {
    const user = JSON.parse(localStorage.getItem('user'));
    const recommendationsArea = document.getElementById('recommendationsArea');
    const personalList = document.getElementById('personalRecommendations');
    const popularList = document.getElementById('popularRecommendations');
    
    if (!recommendationsArea || !popularList) {
        console.error('推荐区域元素未找到');
        return;
    }

    // 移除整体隐藏
    recommendationsArea.classList.remove('hidden');
    
    if (!user) {
        // 未登录时只隐藏个性化推荐部分
        const personalSection = document.querySelector('.recommendation-section:first-child');
        if (personalSection) {
            personalSection.classList.add('hidden');
        }
    }

    // 显示加载状态
    popularList.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i>
            <span>加载中...</span>
        </div>
    `;

    if (user) {
        personalList.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <span>加载中...</span>
            </div>
        `;
    }

    try {
        // 独立处理热门推荐
        const hotResponse = await fetch('/api/articles/hot/', {
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!hotResponse.ok) {
            throw new Error('获取热门推荐失败');
        }
        
        const hotData = await hotResponse.json();
        if (hotData && hotData.length > 0) {
            popularList.innerHTML = hotData.map(article => `
                <div class="recommendation-item">
                    <a href="/article/${article.id}/" class="recommendation-title">${article.title}</a>
                </div>
            `).join('');
        } else {
            popularList.innerHTML = '<div class="no-data">暂无热门文章</div>';
        }
    } catch (error) {
        console.error('获取热门推荐失败:', error);
        popularList.innerHTML = '<div class="error-message">获取推荐失败</div>';
    }

    // 独立处理个性化推荐
    if (user && personalList) {
        try {
            const recommendResponse = await fetch('/api/articles/recommend/', {
                headers: {
                    'Accept': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (!recommendResponse.ok) {
                throw new Error('获取个性化推荐失败');
            }
            
            const recommendData = await recommendResponse.json();
            if (recommendData && recommendData.length > 0) {
                personalList.innerHTML = recommendData.map(article => `
                    <div class="recommendation-item">
                        <a href="/article/${article.id}/" class="recommendation-title">${article.title}</a>
                    </div>
                `).join('');
            } else {
                personalList.innerHTML = '<div class="no-data">暂无推荐</div>';
            }
        } catch (error) {
            console.error('获取个性化推荐失败:', error);
            personalList.innerHTML = '<div class="error-message">获取推荐失败</div>';
        }
    }
}