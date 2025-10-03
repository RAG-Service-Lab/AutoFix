import os, json, re, unicodedata, glob
import pdfplumber
from collections import OrderedDict
import warnings
import logging

warnings.filterwarnings("ignore", message="Could get FontBBox")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# ---------- 텍스트 정리 ----------
def norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("\xa0", " ")
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -:·|")
    return s.strip()

def key_id(s: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", norm(s).lower())

def dedup_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        k = key_id(x)
        if k and k not in seen:
            seen.add(k)
            out.append(norm(x))
    return out

# ---------- 표 파서 ("현상 | 예상 원인" 양식만) ----------
def parse_table_target(page):
    result = OrderedDict() # 비어있는 아이
    tables = page.extract_tables() or []

    for table in tables:
        last_ph = None
        last_cause = None

        if not table or len(table[0]) < 2:
            # print('ccc')
            continue

        header = [norm(x) for x in table[0]]
        #print('🎈🎈', header)
        a = 0
        header_split = []
        found_indices = {}

        for idx, component in enumerate(header) :
            splitted = component.split(" ")
            header_split.extend(splitted)

            if "현상" in splitted:
                found_indices["현상"] = idx
            if "코드" in splitted:
                found_indices["코드"] = idx
            if "원인" in splitted:
                found_indices["원인"] = idx

            # 현대 전처리 
            #if "현상" in splitted:
            #    found_indices["현상"] = idx
            #if "코드" in splitted:
            #    found_indices["코드"] = idx
            #if "원인" in splitted:
            #    found_indices["원인"] = idx
            #if '현' in splitted:
            #    found_indices["현"] = idx
            #if '증상' in splitted:
            #    found_indices["증상"] = idx
            #if '유형' in splitted:
            #    found_indices["유형"] = idx
            #if '고장현상' in splitted:
            #    found_indices["고장현상"] = idx
            #if '점검항목' in splitted:
            #    found_indices["점검항목"] = idx
            #if '고장' in splitted:
            #    found_indices["고장"] = idx

        if (("현상" in found_indices or "코드" in found_indices) and "원인" in found_indices):
          
           # 한 현상이 여러 원인을 가지는 경우 - 합치기
            for row in table[1:]:
                # print('row : ', row)
                if not row or len(row) < 2:   # 해당없음
                    # print('aaa')
                    continue
                idx_ph = found_indices.get("현상", found_indices.get("코드"))
                idx_cause = found_indices["원인"]

            # 한 원인이 여러 결과를 가지는 경우도 합치기
                # ph = norm(row[idx_ph]) if idx_ph is not None and idx_ph < len(row) else None
                # cause = norm(row[idx_cause]) if idx_cause < len(row) else None

                ph_cell = row[idx_ph] if idx_ph is not None and idx_ph < len(row) else ""
                ph = norm(ph_cell).strip() if ph_cell else None
                if ph:
                    last_ph = ph
                else:
                    ph = last_ph  # 빈 값이면 이전 현상 사용

                # 원인 가져오기
                cause_cell = row[idx_cause] if idx_cause is not None and idx_cause < len(row) else ""
                cause = norm(cause_cell).strip() if cause_cell else None
                if cause:
                    last_cause = cause
                else:
                    cause = last_cause  # 빈 값이면 이전 원인 사용

                if ph and cause:
                    result.setdefault(ph, [])
                    if cause not in result[ph]:
                        result[ph].append(cause)
    return result

# ---------- 표 위 텍스트(현상 제목) + 표 매칭 ----------
def parse_table_with_title(page):
    result = OrderedDict()

    # 모든 텍스트 좌표 추출
    words = page.extract_words()
    lines = {}
    for w in words:
        y = round(w["top"])
        lines.setdefault(y, []).append(w["text"])
    sorted_lines = sorted(lines.items(), key=lambda x: x[0])

    # 표 찾기
    tables = page.find_tables()
    for table in tables:
        top_y = table.bbox[1]
        # 표 위쪽 가장 가까운 줄 찾기
        candidates = [line for y, line in sorted_lines if y < top_y]
        if not candidates:
            continue
        title = " ".join(candidates[-1])  # 가장 가까운 줄

        # 표 데이터 추출
        # data = table.extract()
        rows = table.extract() 
        causes = []
        header = [norm(x) for x in rows[0]]
        # print('🎈🎈', header)
        header_split = []
        found_indices = {}
        last_ph = []
        last_cause = []

        for idx, component in enumerate(header) :
            splitted = component.split(" ")
            header_split.extend(splitted)

            if "원인" in splitted:
                found_indices["원인"] = idx
                # print(idx)

        if "원인" in found_indices:
           # 한 현상이 여러 원인을 가지는 경우 - 합치기
            for row in rows[1:]:
                if not row or len(row) < 2:   
                    continue
            
            # 한 원인이 여러 결과를 가지는 경우
                idx_cause = found_indices["원인"]
                
                ph_cell = row[idx_cause] if idx_cause is not None and idx_cause < len(row) else ""
                ph = norm(ph_cell).strip() if ph_cell else None

                if ph:
                    last_ph = ph
                else:
                    ph = last_ph 
                
                # 원인 가져오기
                cause_cell = row[idx_cause] if idx_cause is not None and idx_cause < len(row) else ""
                cause = norm(cause_cell).strip() if cause_cell else None
                if cause:
                    last_cause = cause
                else:
                    cause = last_cause  # 빈 값이면 이전 원인 사용

                if ph and cause:
                    result.setdefault(title, [])
                    if cause not in result[title]:
                        result[title].append(cause)

    return result


# ---------------- 카테고리 추출 ------------------- 
def transform_categories(parts):
    # cats = parts[3:]  # 앞 3개 무시 (ev3~ev6)
    cats = parts
    cats = dedup_keep_order(cats)
    if len(cats) == 2:
        return [cats[0], "없음", "고장진단"]
    elif len(cats) == 3:
        return [cats[0], cats[1], "고장진단"]
    elif len(cats) >= 4:
        return [cats[0], cats[1] + "+" + cats[2], "고장진단"]
    else:
        return []


# ----------------- FaulMap 병합 ---------------------
def merge_faultmaps(dst: dict, src: dict):
    for ph, causes in src.items():
        dst.setdefault(ph, [])
        for c in causes:
            if c not in dst[ph]:
                dst[ph].append(c)


# ---------------- PDF 한개 처리 -----------------------
def parse_pdf(path):
    parent_folder = os.path.basename(os.path.dirname(os.path.abspath(path))) or "ROOT"
    result = {parent_folder: OrderedDict()}
    found_valid = False

    # with pdfplumber.open(path) as pdf:
    # with fitz.open(path) as pdf:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            # header line에서 카테고리 추출
            text = page.extract_text() or ''
            header_line = None
            for line in text.split("\n"):
                if ">" in line:
                    header_line = line
                    break
            if not header_line:
                continue  # > 없는 PDF는 skip

            parts = [norm(p) for p in header_line.split(">")]
            cats = transform_categories(parts)
            concats = '+'.join(cats)

            if not cats:
                continue

            # # 표 데이터 추출
            # table_data = parse_table_target(page)
            # if table_data:
            #     # print('result[parent_folder] : ', result[parent_folder])
            #     print(parent_folder)
            #     print('cats : ', cats)
            #     result[parent_folder].setdefault(concats, {}).update(table_data)
            #     found_valid = True

            # 두 방식 병합
            table_data1 = parse_table_target(page)       # 표 안에 현상이 있는 경우
            table_data2 = parse_table_with_title(page)   # 표 위 제목이 있는 경우
            table_data = {}
            merge_faultmaps(table_data, table_data1)
            merge_faultmaps(table_data, table_data2)

            if table_data:
                result[parent_folder].setdefault(concats, {}).update(table_data)
                found_valid = True


    return result if found_valid else None
    # return table_data if found_valid else None

# ---------- JSON 파일 기호 처리 --------
def clean_dict(obj):
    if isinstance(obj, dict):
        return {k: clean_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_dict(x) for x in obj]
    elif isinstance(obj, str):
        # 불필요한 기호 제거
        return obj.replace("–", "").replace("•", "").strip()
    else:
        return obj

# ---------- 여러 PDF 처리 ----------
def parse_pdfs(folder_path, output_json):
    final_result = OrderedDict()
    pdf_files = glob.glob(os.path.join(folder_path, "**/*.pdf"), recursive=True)
    # print(len(pdf_files))

    for pdf_file in pdf_files:
        data = parse_pdf(pdf_file)
        # print(data)
        if not data:  # 대상 양식 아니면 skip
            continue

        for folder, content in data.items():
            if folder not in final_result:
                final_result[folder] = content
            else:
                for k, v in content.items():
                    final_result[folder].setdefault(k, {}).update(v)

    cleaned_result = clean_dict(final_result)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(cleaned_result, f, ensure_ascii=False, indent=2)

    print("총 PDF 개수:", len(pdf_files))
    print("대상 양식 추출 개수:", sum(1 for pdf in pdf_files if parse_pdf(pdf)))
    print("저장 완료:", output_json)

#---------- json 폴더명 반환 -------------

folder_path = "./kia_data"
subfolders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]

if __name__ == "__main__":

    for a in subfolders : 
        #print('🎈🎈🎈', a)
        folder_path = f"./kia_data/{a}"
        output_file = f"./kia_data_json/{a}.json"    
        #print('😑', folder_path)
        #print('🤖', output_file)               
        parse_pdfs(folder_path, output_file)


# if __name__ == "__main__":
#     folder_path = "./kia_data/ELECTRIFIED,G80(RG3 EV)_136KW+136KW"
#     output_file = "4.json"                    # 항상 같은 이름
#     parse_pdfs(folder_path, output_file)
