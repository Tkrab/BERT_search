import requests
import time
import random
import xlwt
import os
import json


class CoreAPI:
    def __init__(self):
        self.api_key = "NuOQyZcp6BM5iHDvCTdYR4IK7LF2bGft"
        self.base_url = "https://api.core.ac.uk/v3/search/works"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search_papers(self, keywords, max_papers=100):
        all_papers = []
        for keyword in keywords:
            print(f"正在搜索关键词: {keyword}")
            page = 1
            papers_count = 0

            while papers_count < max_papers:
                try:
                    params = {
                        "q": keyword,
                        "page": page,
                        "pageSize": 100,
                        "limit": 100
                    }

                    response = requests.get(
                        self.base_url,
                        headers=self.headers,
                        params=params
                    )

                    if response.status_code == 200:
                        data = response.json()
                        papers = self._process_results(data.get('results', []))
                        if not papers:
                            break

                        all_papers.extend(papers)
                        papers_count += len(papers)
                        print(f"已获取 {papers_count} 篇文献")

                        page += 1
                        time.sleep(20)  # 每次请求间隔20秒
                    else:
                        print(f"API请求失败: {response.status_code}")
                        break

                except Exception as e:
                    print(f"处理数据时出错: {str(e)}")
                    continue

        return all_papers

    def _process_results(self, results):
        processed_papers = []
        for paper in results:
            try:
                data = []
                # 提取标题
                data.append(paper.get('title', '无标题'))
                # 提取作者
                authors = ', '.join([author.get('name', '') for author in paper.get('authors', [])])
                data.append(authors if authors else '未知作者')
                # 提取摘要
                data.append(paper.get('abstract', '无摘要'))
                # 提取下载链接
                download_url = paper.get('downloadUrl', '')
                data.append(download_url)
                # 提取年份
                data.append(str(paper.get('yearPublished', '未知年份')))

                # 下载PDF
                if download_url:
                    pdf_path = self.download_pdf(download_url, data[0])
                    if pdf_path:
                        print(f"PDF下载成功: {pdf_path}")
                    else:
                        print(f"PDF下载失败: {data[0]}")

                processed_papers.append(data)
                print(f"成功处理文章: {data[0]}")

            except Exception as e:
                print(f"处理文章数据时出错: {str(e)}")
                continue

        return processed_papers

    def download_pdf(self, url, title):
        try:
            valid_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{valid_title[:100]}.pdf"
            filepath = os.path.join(r"D:\毕设\search_bert\data\paper", filename)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/pdf"
            }

            response = requests.get(url, headers=headers, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                time.sleep(20)  # 每次下载后等待20秒
                return filepath
        except Exception as e:
            print(f"下载PDF时出错: {str(e)}")
        return None


def saveData(datalist, savepath):
    print("正在保存数据...")
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)
    sheet = book.add_sheet('学术文献数据', cell_overwrite_ok=True)
    col = ("标题", "作者", "摘要", "下载链接", "发布年份")

    for i in range(len(col)):
        sheet.write(0, i, col[i])

    for i in range(len(datalist)):
        data = datalist[i]
        for j in range(len(data)):
            sheet.write(i + 1, j, data[j])

    book.save(savepath)
    print(f"数据已保存至: {savepath}")


def main():
    # 创建PDF保存目录
    pdf_dir = r"D:\毕设\search_bert\data\paper"
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    api = CoreAPI()
    keywords = ["sailing"]
    papers = api.search_papers(keywords)

    if papers:
        savepath = r"D:\毕设\search_bert\data\core_papers.xls"
        saveData(papers, savepath)
    else:
        print("未获取到数据")


if __name__ == "__main__":
    main()
    print("爬取完毕！")