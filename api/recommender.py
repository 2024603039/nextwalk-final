"""NEXTWORK weighted matching; demo CSV is synthetic, not verified vacancies."""
from pathlib import Path
from math import radians, sin, cos, asin, sqrt
import csv

DATA = Path(__file__).parent / 'data' / 'gongju_jobs.csv'
REGIONS = {'신관동':(36.4714,127.1353),'중동':(36.4509,127.1231),'웅진동':(36.4603,127.1118),'금학동':(36.4370,127.1250),'옥룡동':(36.4536,127.1433),'월송동':(36.4800,127.1530),'공주시':(36.4465,127.1190)}
GROUPS = {'운전':['운전','택배','배송','배달','물류','차량','주차','기사'],'사무':['사무','행정','접수','문서','안내'],'시설':['시설','경비','보안','관리','점검'],'돌봄':['돌봄','요양','복지','간병'],'청소':['청소','미화','환경'],'조리':['조리','급식','주방','식당'],'판매':['판매','매장','고객','계산']}

def group_of(s):
    s=str(s).lower()
    for group, words in GROUPS.items():
        if any(w in s for w in words): return group
    return None

def km(a,b):
    lat1,lon1=map(radians,a);lat2,lon2=map(radians,b)
    x=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 6371.0088*2*asin(min(1,sqrt(x)))

def match_score(query, text, max_points):
    if not query: return 0
    if query.lower() in text.lower(): return max_points
    a,b=group_of(query),group_of(text)
    return round(max_points*0.67) if a and a==b else 0

def recommend_jobs(previous_job='', experience_years=0, preferred_region='', work_type='', desired_job='', preferred_category='', limit=5, min_score=60, latitude=None, longitude=None):
    category=desired_job or preferred_category
    if latitude is not None and longitude is not None: center=(float(latitude),float(longitude))
    elif preferred_region in REGIONS: center=REGIONS[preferred_region]
    elif preferred_region: raise ValueError('지원하지 않는 지역입니다. 신관동, 중동, 웅진동, 금학동, 옥룡동, 월송동, 공주시 중 선택하거나 위도/경도를 입력하세요.')
    else: center=None
    results=[]
    with DATA.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        text=' '.join([row['직무'],row['관련경력'],row['분야'],row['설명']])
        career=match_score(previous_job,text,30)
        field=match_score(category,text,25)
        work=15 if work_type and work_type==row['근무형태'] else (8 if work_type and (work_type in row['근무형태'] or row['근무형태'] in work_type) else 0)
        distance=km(center,(float(row['위도']),float(row['경도']))) if center else None
        location=30 if distance is not None and distance<=10 else 20 if distance is not None and distance<=20 else 10 if distance is not None and distance<=30 else 0
        score=career+field+work+location
        if score>=min_score:
            results.append({'job':row['직무'],'region':row['지역'],'score':score,'distance_km':round(distance,2) if distance is not None else None,'grade':'매우 적합' if score>=80 else '적합','score_details':{'career':career,'location':location,'category':field,'work_type':work},'work_type':row['근무형태'],'salary':row['보수'],'reason':f'경력 {career}점, 거리 {location}점, 분야 {field}점, 근무형태 {work}점','source':row['출처'],'posting_url':row['공고링크']})
    results.sort(key=lambda x:(-x['score'],x['distance_km'] if x['distance_km'] is not None else 1e6))
    return {'status':'ok','data_type':'synthetic_demo','total_candidates':len(rows),'matched_count':len(results),'recommendations':results[:limit], 'method':'career 30 + distance 30 + category 25 + work 15', 'note':'채용공고는 기능 검증용 가상 데이터입니다. 경력 연수는 채용 요건 데이터가 없어 점수에 반영하지 않습니다.'}
