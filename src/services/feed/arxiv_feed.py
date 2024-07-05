import urllib.request
import feedparser
import pandas as pd
from datetime import datetime

# arXiv API URL 설정
base_url = 'http://export.arxiv.org/api/query?'

# 컴퓨터 비전 분야의 논문을 검색하는 쿼리
search_query = 'cat:cs.CV'

# 결과를 저장할 빈 리스트
papers = []

# 10,000개의 결과를 수집하기 위해 반복 실행
total_results = 10000
results_per_request = 100
for start in range(0, total_results, results_per_request):
    # 쿼리 문자열을 URL 인코딩
    query_params = f'search_query={search_query}&start={start}&max_results={results_per_request}'
    url = base_url + query_params

    # URL을 통해 데이터 요청 및 응답 받기
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')

    # 받은 데이터를 feedparser를 사용해 파싱
    feed = feedparser.parse(data)

    # 데이터를 리스트에 추가
    for entry in feed.entries:
        papers.append({
            'Title': entry.title,
            'Authors': ', '.join(author.name for author in entry.authors),
            'Published': entry.published,
            'Abstract': entry.summary,
            'Link': entry.link
        })

# 데이터를 DataFrame으로 변환
df = pd.DataFrame(papers)

# 현재 날짜와 시간을 파일 이름에 포함
current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
filename = f"arxiv_papers_{search_query.replace(':', '_').replace(' ', '_')}_{current_time}.csv"

# CSV 파일로 저장
df.to_csv(filename, index=False)
print(f"Saved to {filename}")
