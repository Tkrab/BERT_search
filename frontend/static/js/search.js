// 修改搜索参数对象，添加新的搜索条件
let searchParams = {
    q: '',
    category: '',
    source_type: '',
    author: '',           // 添加作者参数
    date_start: '',       // 添加开始日期参数
    date_end: '',         // 添加结束日期参数
    page: 1,
    page_size: 10
};

document.addEventListener('DOMContentLoaded', () => {
    initSearchTypeTab();
    initSearchForm();
    initFilterEvents();
    initPagination(); 
    initAdvancedSearchOptions(); // 添加这一行
    
    const urlParams = new URLSearchParams(window.location.search);
    const keyword = urlParams.get('keyword');
    if (keyword) {
        document.querySelector('.main-search-input').value = keyword;
        searchParams.q = keyword;
        performSearch();
    }
});

// 添加高级搜索选项的初始化函数
function initAdvancedSearchOptions() {
    // 作者输入框事件
    const authorInput = document.getElementById('author');
    authorInput.addEventListener('change', (e) => {
        searchParams.author = e.target.value.trim();
    });
    
    // 日期范围输入框事件
    const dateStartInput = document.getElementById('publish-date-start');
    const dateEndInput = document.getElementById('publish-date-end');
    
    dateStartInput.addEventListener('change', (e) => {
        searchParams.date_start = e.target.value;
    });
    
    dateEndInput.addEventListener('change', (e) => {
        searchParams.date_end = e.target.value;
    });
}

// 修改搜索表单初始化函数，确保高级搜索选项也被包含
function initSearchForm() {
    const searchForm = document.querySelector('.search-box-container');
    const searchInput = document.querySelector('.main-search-input');
    const searchButton = document.querySelector('.main-search-button');

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchParams.q = searchInput.value;
            searchParams.page = 1;  // 重置页码
            performSearch();
        }
    });

    // 保留按钮点击事件
    searchButton.addEventListener('click', (e) => {
        e.preventDefault();
        searchParams.q = searchInput.value;
        searchParams.page = 1;  // 重置页码
        performSearch();
    });
}

function initPagination() {
    const pagination = document.querySelector('.pagination');
    
    pagination.addEventListener('click', (e) => {
        const button = e.target.closest('.page-button');
        if (!button || button.disabled) return;
        
        const newPage = parseInt(button.dataset.page);
        if (!isNaN(newPage)) {
            console.log('切换到页码:', newPage);  // 添加日志
            searchParams.page = newPage;
            performSearch();
        }
    });
}

async function performSearch() {
    try {
        const token = localStorage.getItem('token');
        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // 显示加载提示
        const loadingIndicator = document.getElementById('loading-indicator');
        const resultsList = document.querySelector('.results-list');
        loadingIndicator.style.display = 'block';
        resultsList.style.opacity = '0.5';

        searchParams.page = parseInt(searchParams.page) || 1;
        
        // 构建搜索 URL
        const searchUrl = new URL('/api/articles/search/', window.location.origin);
        Object.keys(searchParams).forEach(key => {
            const value = searchParams[key];
            if (value !== '' && value !== null && value !== undefined) {
                searchUrl.searchParams.append(key, value);
            }
        });
        
        // 执行搜索请求
        const searchResponse = await fetch(searchUrl, {
            headers: headers,
            credentials: 'include'
        });
        
        const searchData = await searchResponse.json();
        
        // 修改调试日志，直接查看完整的文章数据结构
        console.log('搜索结果数据:', searchData);
        console.log('第一篇文章数据:', searchData.results[0]);
        
        // 从搜索结果中提取分类统计数据
        const categoryStats = extractCategoryStats(searchData.results);
        console.log('提取的分类统计:', categoryStats);
        
        updateFilterSidebar(categoryStats);
        updateSearchResults(searchData);

        // 隐藏加载提示并恢复结果列表透明度
        loadingIndicator.style.display = 'none';
        resultsList.style.opacity = '1';
    } catch (error) {
        console.error('搜索失败:', error);
        // 发生错误时也要隐藏加载提示
        const loadingIndicator = document.getElementById('loading-indicator');
        const resultsList = document.querySelector('.results-list');
        loadingIndicator.style.display = 'none';
        resultsList.style.opacity = '1';
    }
}

// 新增：从搜索结果中提取分类统计数据
function extractCategoryStats(results) {
    const categoryCount = {};
    const sourceTypeCount = {};
    
    results.forEach(article => {
        // 修改为使用 category_name 字段
        if (article.category_name) {
            const categoryName = article.category_name;
            categoryCount[categoryName] = (categoryCount[categoryName] || 0) + 1;
        }
        
        // 统计来源类型
        if (article.source_type) {
            sourceTypeCount[article.source_type] = (sourceTypeCount[article.source_type] || 0) + 1;
        }
    });

    // 如果分类数据为空，添加一个默认分类
    if (Object.keys(categoryCount).length === 0) {
        categoryCount['全部'] = results.length;
    }

    return {
        categories: Object.entries(categoryCount).map(([name, count]) => ({ name, count })),
        source_types: Object.entries(sourceTypeCount).map(([source_type, count]) => ({ source_type, count }))
    };
}

function updateFilterSidebar(data) {
    const categoryList = document.querySelector('.filter-section:first-child .filter-list');
    categoryList.innerHTML = data.categories.map(cat => `
        <li>
            <label class="filter-item">
                <input type="checkbox" value="${cat.name}" 
                       ${searchParams.category === cat.name ? 'checked' : ''}>
                ${cat.name} <span>(${cat.count})</span>
            </label>
        </li>
    `).join('');

    // 更新来源类型
    const sourceTypeList = document.querySelector('.filter-section:last-child .filter-list');
    sourceTypeList.innerHTML = data.source_types.map(type => `
        <li>
            <label class="filter-item">
                <input type="checkbox" value="${type.source_type}"
                       ${searchParams.source_type === type.source_type ? 'checked' : ''}>
                ${type.source_type} <span>(${type.count})</span>
            </label>
        </li>
    `).join('');
}

// 修改 updatePagination 函数，确保分页链接包含所有搜索参数
function updatePagination(data) {
    const pageButtons = document.querySelector('.page-buttons');
    
    const currentPage = parseInt(searchParams.page);
    const totalPages = Math.ceil(data.count / searchParams.page_size);
    
    const pageInfoText = `第${currentPage}/${totalPages}页`;
    document.querySelector('.page-info').textContent = pageInfoText;
    
    let buttons = [];
    
    buttons.push(`<button class="page-button" data-page="${currentPage - 1}" ${currentPage <= 1 ? 'disabled' : ''}>上一页</button>`);
    
    if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) {
            buttons.push(`<button class="page-button ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`);
        }
    } else {
        if (currentPage <= 3) {
            for (let i = 1; i <= 5; i++) {
                buttons.push(`<button class="page-button ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`);
            }
            buttons.push('<span>...</span>');
            buttons.push(`<button class="page-button" data-page="${totalPages}">${totalPages}</button>`);
        } else if (currentPage >= totalPages - 2) {
            buttons.push(`<button class="page-button" data-page="1">1</button>`);
            buttons.push('<span>...</span>');
            for (let i = totalPages - 4; i <= totalPages; i++) {
                buttons.push(`<button class="page-button ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`);
            }
        } else {
            buttons.push(`<button class="page-button" data-page="1">1</button>`);
            buttons.push('<span>...</span>');
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                buttons.push(`<button class="page-button ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`);
            }
            buttons.push('<span>...</span>');
            buttons.push(`<button class="page-button" data-page="${totalPages}">${totalPages}</button>`);
        }
    }
    
    // 下一页按钮
    buttons.push(`<button class="page-button" data-page="${currentPage + 1}" ${currentPage >= totalPages ? 'disabled' : ''}>下一页</button>`);
    
    pageButtons.innerHTML = buttons.join('');
    
    // 以下代码有语法错误，需要删除或修正
    // 构建分页URL时包含所有搜索参数
    // 这段代码似乎是从后端代码复制过来的，在前端JS中不适用
    // let baseUrl = `/api/articles/search/?q=${searchParams.q}`;
    // if (searchParams.category) baseUrl += `&category=${searchParams.category}`;
    // if (searchParams.source_type) baseUrl += `&source_type=${searchParams.source_type}`;
    // if (searchParams.author) baseUrl += `&author=${searchParams.author}`;
    // if (searchParams.date_start) baseUrl += `&date_start=${searchParams.date_start}`;
    // if (searchParams.date_end) baseUrl += `&date_end=${searchParams.date_end}`;
    // if (sort) baseUrl += `&sort=${sort}`;
    
    // response_data = {
    //     'count': total_count,
    //     'next': `${baseUrl}&page=${page + 1}` if end < total_count else null,
    //     'previous': `${baseUrl}&page=${page - 1}` if page > 1 else null,
    //     'results': serializer.data
    // }
}

function updateSearchResults(data) {
    const resultsList = document.querySelector('.results-list');
    const countElement = document.querySelector('.count-number');
    
    countElement.textContent = data.count;
    
    resultsList.innerHTML = data.results.map(article => `
        <div class="result-item">
            <div class="result-content">
                <h3 class="result-title">
                    <a href="/article/${article.id}/">${article.title}</a>
                </h3>
                <div class="result-meta">
                    <span class="author">${article.author || '未知作者'}</span>
                    <span class="source">${article.source || '未知来源'}</span>
                    <span class="date">${new Date(article.created_at).toLocaleDateString()}</span>
                </div>
                <div class="result-abstract">
                    ${article.abstract ? article.abstract.substring(0, 200) + '...' : '暂无摘要'}
                </div>
            </div>
        </div>
    `).join('');
    
    updatePagination(data);
}

function initSearchTypeTab() {
    const searchTypeTabs = document.querySelector('.search-type-tabs');
    if (!searchTypeTabs) {
        console.warn('未找到搜索类型选项卡元素');
        return;
    }
    
    searchTypeTabs.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-button')) {
            // 移除其他按钮的 active 类
            searchTypeTabs.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            // 为当前点击的按钮添加 active 类
            e.target.classList.add('active');
            
            searchParams.q = document.querySelector('.main-search-input').value;
            performSearch();
        }
    });
}

function initSearchForm() {
    const searchForm = document.querySelector('.search-box-container');
    const searchInput = document.querySelector('.main-search-input');
    const searchButton = document.querySelector('.main-search-button');

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchParams.q = searchInput.value;
            searchParams.page = 1;  // 重置页码
            performSearch();
        }
    });

    // 保留按钮点击事件
    searchButton.addEventListener('click', (e) => {
        e.preventDefault();
        searchParams.q = searchInput.value;
        searchParams.page = 1;  // 重置页码
        performSearch();
    });
}

function initFilterEvents() {
    document.getElementById('categoryList').addEventListener('change', (e) => {
        if (e.target.type === 'checkbox') {
            searchParams.category = e.target.checked ? e.target.value : '';
            searchParams.page = 1;  // 重置页码为1
            performSearch();
        }
    });

    document.getElementById('sourceTypeList').addEventListener('change', (e) => {
        if (e.target.type === 'checkbox') {
            searchParams.source_type = e.target.checked ? e.target.value : '';
            searchParams.page = 1;  // 重置页码为1
            performSearch();
        }
    });
}
