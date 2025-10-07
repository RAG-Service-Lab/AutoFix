import re
import kss
import json
import unicodedata


def clean_doc(s, kin=False, is_title=False):
    if not s:
        return ""
    
    # 1. 유니코드 정규화 (호환 문자 통합)
    s = unicodedata.normalize("NFKC", str(s))
    
    # 2. 제어문자 제거 (Zero-width, 방향 제어 등)
    s = re.sub(r'[\u200b-\u200f\u202a-\u202e\x00-\x1F\x7F]', '', s)
    
    # 3. 전화번호 제거
    s = re.sub(r"\b\d{2,4}-\d{3,4}-\d{4}\b", " ", s)   # 010-1234-5678
    s = re.sub(r"\b\d{9,11}\b", " ", s)                # 01012345678
    s = re.sub(r"\+?\d{1,3}-\d{1,4}-\d{3,4}-\d{4}", " ", s)  # 국제번호
    s = re.sub(r"\(?0\d{1,2}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", " ", s) # (031)395-5182, 031)395-5182, 031 395 5182

    # 4. 주소 제거
    s = re.sub(r"[가-힣]+(로|길|번길)\s?\d+(-\d+)?", " ", s)
    s = re.sub(r"[가-힣]+(시|군|구|읍|면|동)\s?[가-힣0-9]*", " ", s)
    
    # 5. URL 제거
    s = re.sub(r"http[s]?://\S+|www\.\S+|blog\.naver\.com\S*", " ", s)
    
    # 6. 해시태그 제거
    s = re.sub(r"#\S+", " ", s)

    # 7. 알파벳, 한글, 숫자, 공백, 괄호, 대괄호, 콜론, 하이픈만 남기고 나머지는 제거
    s = re.sub(r"[^0-9a-zA-Z가-힣\s\(\)\[\]\.: \-]+", " ", s)

    # 8. 공백 정리
    s = re.sub(r"\s+", " ", s).strip()

    if is_title or not kin:
        return s

    else:
        sentences = re.split(r'(?<=[.?!])\s+', s)
        # 제거할 광고문구
        remove_phrases = ["맡겨주세요", "감사합니다", "노력하겠습니다", "함께 하세요", "상담", "문의" ]
        
        # 마지막 문장 + 특정 문구 포함 문장 제거
        filtered_sentences = []
        for i, sent in enumerate(sentences):
            if i == len(sentences) - 1:  # 마지막 문장 제거
                    continue
            if any(phrase in sent for phrase in remove_phrases):
                continue
            filtered_sentences.append(sent)
        
        # 문장 재결합
        s = ' '.join(filtered_sentences)
        
        return s


def no_period(text: str, threshold: float = 0.01) -> bool:
    """
    문단이 마침표/느낌표/물음표로 구분되지 않은 경우 True 반환
    threshold: 문장부호 비율 (0.1 = 글자 수 대비 10% 미만이면 '문단 구분이 없다'고 판단)
    """
    text = text.strip()
    if not text:
        return False
    
    # 문장부호 개수
    punct_count = sum(text.count(p) for p in ".?!")
    
    # 전체 글자 수 대비 문장부호 비율
    ratio = punct_count / max(len(text), 1)
    # print('전체 글자 수 대비 문장부호 비율: ', ratio)
    return punct_count == 0 or ratio < threshold


if __name__ == "__main__":
    new_contents = []
    black_list = []

    # path = "merged_data/total_blog_data.json"
    path = "merged_data/total_kin_data.json"

    with open(path, 'r',  encoding='utf-8') as f:
        total = json.load(f)

    with open("./backup/blacklist.txt", "r", encoding="utf-8") as f:
        black_list = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print(len(total))
    print(len(black_list))

    black_words = ['마우스', '로지텍', '오토바이', '키보드', '모니터', '맥미니', '노트북', '컴퓨터',
                    '소파', '의자', '책상', '유모차', '자전거', '청소기', '펀딩', '오메가', 'AI', '운동',
                        '게임', '영화', '사이버', '사자성어', '키우기', '배그', '인라인', '괴담', '레고',
                        '인쇄기', '어린이', '핸드폰', '강아지', '고양이', '동물', '정수기', '비스포크', '포토',
                            '디퓨저', '캣휠', '햄스터', '프로젝터', '캐리어', '세차', '스케이트', '슈즈', '승강기',
                                '신제품', '잡담', '수업', '발명', '아수스', '레노버', '시계', '바이크', '남자', '여자',
                                    '영상', '드론', '건조기', '세탁기', '수트', '세그웨이', '킥보드', 'PC', '미디어', '가전',
                                    'Computer', 'GTA', '여행', '요가', 'TV', '한글', '선풍기', '철학', '파노라마', '한의원', '리뷰',
                                    '배틀그라운드', '서버', '한자', '건물']

    black_words = [unicodedata.normalize("NFKC", w.lower()) for w in black_words]

    for idx, content in enumerate(total):
        # check = no_period(content['content'])
        # if check or idx in black_list or 'chho2050' in content['link']: # 마침표 없는 문장으로 이루어진 글 / 자동차와 무관한 글 / 일반적인 글 형식이 아닌 내용
            # continue

        title = unicodedata.normalize("NFKC", content['title'].lower())

        if any(word in title for word in black_words):
            continue

        print(f"{idx} 번 데이터 제목: {content['title'][:20]}")

        content['title'] = clean_doc(content['title'], kin=True, is_title=True)
        content['content'] = clean_doc(content['content'], kin=True)

        new_contents.append(content)

    print(len(new_contents))

    with open('merged_data/cleaned_kin_data.json', 'w', encoding='utf-8') as f:
        json.dump(new_contents, f, ensure_ascii=False, indent=4)