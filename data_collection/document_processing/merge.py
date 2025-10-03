import json, glob

#--------- 차 type 별 json merge ----------------
def merge_json_dicts_to_list(file_list, output_file):
    merged = []
    for f in file_list:
        with open(f, encoding="utf-8") as infile:
            data = json.load(infile)
            if isinstance(data, dict):  # dict 구조만 추가
                merged.append(data)
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(merged, outfile, ensure_ascii=False, indent=2)

# 폴더에 있는 모든 JSON 합치기
files = glob.glob("./hyundai_data_json/*.json")  # kia_data_json
merge_json_dicts_to_list(files, "merged_hyundai.json")


#---------- meta data 형식으로 변환 ----------
def parse_json(data_list):
    result = {"고장진단": []}

    for data in data_list:   # 리스트 안에 각 차종 dict
        for model_engine, categories in data.items():   # EV3(SV1)_150kW
            model, engine = model_engine.split("_", 1)

            for category_key, data in categories.items():    # "2026+150KW+드라이브 샤프트 및 액슬+고장진단"
                # "고장진단" 제거
                clean_category = category_key.replace("고장진단", "").strip("+ ").replace('+', " ").replace('–', " ").strip(' ')

                for state, causes in data.items():
                    state = state.replace('–', ' ').strip('– ').replace('•', ' ').strip(' ')
                    entry = {
                        "title": f"{clean_category} {state}".strip(" -"),
                        "content": ", ".join(causes),  # 리스트 → 콤마 구분 문자열
                        "type": "hyundai",
                        "차종": model,
                        "엔진": engine,
                    }
                    result["고장진단"].append(entry)
    return result

if __name__ == "__main__":
    
    # JSON 불러오기
    with open("merged_hyundai_2.json", "r", encoding="utf-8") as f:
        merged_file = json.load(f)

    parsed = parse_json(merged_file)

    # 결과 저장
    with open("parsed_hyundai.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    print("저장 완료: parsed_hyundai.json")


#----------- hyundai & kia 메타데이터 merge -----
# 파일 두개 불러오기
with open("parsed_hyundai.json", "r", encoding="utf-8") as f1:
    list1 = json.load(f1)   # [ {..}, {..}, ... ]

with open("parsed_kia.json", "r", encoding="utf-8") as f2:
    list2 = json.load(f2)   # [ {..}, {..}, ... ]

# 두 리스트 합치기
merged = list1['고장진단'] + list2['고장진단']   # extend() 써도 동일

merged_data = {'고장진단' : merged}

# 새로운 파일로 저장
with open("parsed_data.json", "w", encoding="utf-8") as out:
    json.dump(merged_data, out, ensure_ascii=False, indent=2)

print(f"합친 개수: {len(merged_data)}")