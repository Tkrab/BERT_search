from document_clustering import DocumentClustering

def main():
    # 指定数据文件夹路径
    data_path = 'paper_txt'
    
    # 创建聚类器（设置期望的聚类数量）
    clustering = DocumentClustering(data_path, n_clusters=5)
    
    # 执行聚类
    clusters = clustering.cluster_documents()

if __name__ == '__main__':
    main()