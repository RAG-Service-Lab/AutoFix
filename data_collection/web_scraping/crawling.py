import re
import requests
from bs4 import BeautifulSoup

def get_parser(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 200 아니면 HTTPError 발생
        return BeautifulSoup(response.text, "html.parser")

    except requests.exceptions.HTTPError as e:
        print(f"[HTTP 오류] 상태코드: {e.response.status_code}, 사유: {e.response.reason}")

    except requests.exceptions.ConnectionError as e:
        print("[네트워크 오류] 서버에 연결할 수 없음:", e)

    except requests.exceptions.Timeout:
        print("[타임아웃 오류] 서버 응답 지연")

    except requests.exceptions.RequestException as e:
        print("[알 수 없는 오류]", e)

    return None

def get_kin_content(url):
    # soup = BeautifulSoup(response.content, 'html.parser')
    bs = get_parser(url)

    if bs == None:
        return "제목 없음", "질문 없음", "답변 없음"

    qna_title = bs.find("div", class_="endTitleSection")
    qna_title_text = qna_title.get_text(strip=True) if qna_title else "제목 없음"

    qna_question = bs.find("div", class_="questionDetail")
    qna_question_text = qna_question.get_text(" ", strip=True) if qna_question else "질문 없음"

    qna_answers = bs.find_all("div", class_="answerDetail _endContents _endContentsText")
    if qna_answers:
        answer_texts = [ans.get_text(" ", strip=True) for ans in qna_answers]
    else:
        qna_answers = bs.find_all("div", class_="se-main-container")

        if qna_answers:
            answer_texts = [ans.get_text(" ", strip=True) for ans in qna_answers]
        else:
            answer_texts = ["답변 없음"]
    
    return qna_title_text, qna_question_text, answer_texts

def get_naver_content(url):

    base_url = "https://blog.naver.com"
    bs = get_parser(url)

    iframe = bs.find("iframe", {"id": "mainFrame"})
    if iframe:
        iframe_src = base_url + iframe["src"]
        bs2 = get_parser(iframe_src)
        content = bs2.find("div", class_="se-main-container")

    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_mobile_naver_content(url):

    url = url.replace("blog.naver.com", "m.blog.naver.com")

    bs = get_parser(url)

    if bs == None:
        return "제목 없음", "내용 없음"

    title_tag = (
        bs.find("h3", class_="se_textarea") or
        bs.find("div", class_="se-title-text") or
        bs.find("div", id="title") or
        bs.find("strong") or
        bs.find("title")  # 최후 fallback: HTML <title> 태그
    )
    title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

    texts = None

    content = bs.find("div", class_="se-main-container")
    if content:
        texts = content.get_text(" ", strip=True)

    if not texts:
        wraps = bs.find_all("div", class_="se_component_wrap")
        if wraps:
            texts = " ".join([w.get_text(" ", strip=True) for w in wraps])

    if not texts:
        legacy = (
            bs.find("div", id="postViewArea") or
            bs.find("div", class_="post-view") or
            bs.find("div", id="viewTypeSelector")
        )
        if legacy:
            texts = legacy.get_text(" ", strip=True)

    if not texts:
        return title, "내용 없음"

    clean_text = re.sub(r'\s+', ' ', texts)
    return title, clean_text

def get_tistory_content(url):
    bs = get_parser(url)

    title_tag = (
        bs.find("h1", class_="tit_blog") or
        bs.find("h2", class_="tit_blog") or
        bs.find("h1", class_="entry-title") or
        bs.find("h2", class_="entry-title") or
        bs.find("title")
    )
    title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

    content = bs.find("div", class_="article") or bs.find("div", class_="tt_article_useless_p_margin")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return title, clean_text
    else: 
        return title, "내용 없음" 

def get_brunch_content(url):
    bs = get_parser(url)
    content = bs.find("div", class_="wrap_body")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_velog_content(url):
    bs = get_parser(url)
    content = bs.find("div", class_="sc-article-content") or bs.find("article")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"
    
def get_egloos_content(url):
    bs = get_parser(url)
    content = bs.find("div", id="entry_text")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_daum_blog_content(url):
    bs = get_parser(url)
    iframe = bs.find("iframe")
    if iframe:
        iframe_url = iframe["src"]
        bs2 = get_parser(iframe_url)
        content = bs2.find("div", class_="blogview_content")
    else:
        content = bs.find("div", class_="blogview_content")

    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_autospy_content(url):
    bs = get_parser(url)
    content = bs.find("div", class_="bbs-view-content") or bs.find("div", class_="board-content")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_encar_content(url):
    bs = get_parser(url)
    content = bs.find("div", class_="board__contents")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_bobaedream_content(url):
    bs = get_parser(url)
    content = bs.find("div", id="bbsContent")
    if content:
        result = content.get_text(" ", strip=True)
        clean_text = re.sub(r'\s+', ' ', result)
        return clean_text
    else: 
        return "내용 없음"

def get_content(component):
    
    blog_url = component['link']
    blog_kind = component['displayLink'].lower()

    if "blog.naver.com" in blog_kind:
        title, content = get_mobile_naver_content(blog_url)
        return title, content
    elif "tistory.com" in blog_kind:
        title, content = get_tistory_content(blog_url)
        return title, content
    else:
        return "unknown"