import json
import time
import ast
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

path = "./merged_data/total_blog_data.json"
with open(path, 'r',  encoding='utf-8') as f:
    blog_total = json.load(f)

print(len(blog_total))

black_list = []
title_dict = {}

instruction = """
당신은 자동차와 관련없는 제목을 걸러내는 노련한 필터입니다.

- 입력은 JSON 형식으로 주어집니다.
- 각 key는 id, value는 글 제목입니다.
- 자동차와 무관한 글 제목의 id만 리스트로 출력하세요.
- 반드시 Python 리스트 형태로 출력하세요. (예: [1, 3, 5])
"""

for idx, content in enumerate(blog_total):
    if idx < 19001:
        continue

    title = content['title']
    if len(title) > 300:
        print(f"{idx}번째 제목 건너뜀 (너무 김: {len(title)}자)")
        continue
    title_dict[f'{idx}'] = title

    if idx % 100 == 0 and idx > 0:
        try:
            time.sleep(2)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": json.dumps(title_dict, ensure_ascii=False)},
                ],
                
                temperature=0,
                max_tokens=1000
            )

            filtered_id = response.choices[0].message.content.strip()

            try:
                ids = ast.literal_eval(filtered_id)
                black_list.extend(ids)
            except Exception as e:
                print(f"리스트 파싱 오류: {filtered_id}, 에러: {e}")

            title_dict = {}
            print(f"{idx}번째까지 완료")

        except Exception as e:
            print(f"{idx}번째 처리 중 오류 발생: {e}")
            print("해당 차례는 건너뜀")
            continue
    
    if idx % 1000 == 0 and idx > 0:
        with open(f"./backup/blacklist_checkpoint_{idx}.txt", "w", encoding="utf-8") as f:
            for item in black_list:
                f.write(str(item) + "\n")
        print(f"{idx}번째까지 blacklist 백업 저장 완료")

with open(f"./backup/blacklist.txt", "w", encoding="utf-8") as f:
    for item in black_list:
        f.write(str(item) + "\n")
print(f"blacklist 최종 저장 완료")