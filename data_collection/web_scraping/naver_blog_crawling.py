import os
import sys
import urllib.request
from dotenv import load_dotenv
from crawling import get_mobile_naver_content
import json

# 키워드 json 파일로 가져오기 → 리스트로 뽑기
keyword_path = './data/keywords.txt'

with open(keyword_path, "r", encoding='utf-8') as f:
    lines = f.readlines()

common_keyword = [line.strip().split('. ', 1)[-1] for line in lines if line.strip()]

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# 딕셔너리 생성
results = {}

# 위에서 가져온 키워드 리스트 for문 돌려서 크롤링(일단 100개)
for kw in common_keyword[:3]:
    contents = []
    seen_links = set()

    for start in range(1, 1000, 100):
        encText = urllib.parse.quote(kw)
        url = f"https://openapi.naver.com/v1/search/blog.json?query={encText}&display=100&start={start}"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        request.add_header("User-Agent", 'Mozilla/5.0 (Windows NT 10.0;Win64; x64)\
                            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98\
                            Safari/537.36')
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        if(rescode==200):
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))

            for item in result["items"]:
                link = item.get('link')
                if not link or link in seen_links:
                    continue
                blog_title, blog_content = get_mobile_naver_content(link)
                if blog_content != "내용 없음":
                        content = {'title': blog_title, 'content': blog_content, 'type': '블로그', '출처': link, '차종': 'None', '엔진': 'None'}
                        contents.append(content)
                        seen_links.add(link)

                results[kw] = contents

        else:
            print("Error Code:" + rescode)

    print(f"키워드 {kw}에는 총 {len(contents)} 개 결과 존재")

# json 파일로 저장하기
with open("results/naver_blog_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("JSON 파일로 저장 완료")