import html
import os
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title='NEXTWORK | 공주의 새로운 기회', page_icon='🧭', layout='wide', initial_sidebar_state='expanded')

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'Manrope','Noto Sans KR',sans-serif}
.stApp{background:#f4f7fc;color:#15243b}
.block-container{padding-top:2rem;max-width:1500px}
[data-testid="stSidebar"]{background:#101d38}
[data-testid="stSidebar"] *{color:#eef4ff!important}
.hero{padding:38px 42px;border-radius:25px;background:linear-gradient(115deg,#101d38,#2149a3 78%,#4678d9);color:white;margin-bottom:25px;box-shadow:0 18px 38px #19366a24}
.hero h1{font-size:42px;font-weight:800;letter-spacing:-1.5px;margin:8px 0;color:white}
.hero p{color:#dce8ff;font-size:17px;line-height:1.7}
.eyebrow{font-size:13px;letter-spacing:2px;font-weight:800;color:#9ec6ff}
.kpi{padding:24px;border-radius:18px;background:white;border:1px solid #e7edf8;box-shadow:0 7px 22px #18315b0b}
.kpi .label{font-size:14px;color:#6c7890}.kpi .num{font-size:30px;font-weight:800;color:#183a85;margin-top:6px}
.job{background:white;border:1px solid #e5eafa;border-radius:17px;padding:20px 22px;margin-bottom:14px;box-shadow:0 6px 20px #203f7609}
.job .title{font-weight:800;font-size:20px;color:#172b51;margin-top:10px}.job .meta{color:#65738b;font-size:14px;margin-top:8px;line-height:1.9}
.badge{display:inline-block;background:#eaf1ff;color:#2756b7;padding:5px 10px;border-radius:9px;font-size:12px;font-weight:700}
.note{background:#fff8e9;padding:12px 18px;border-radius:12px;color:#74551b;font-size:14px;margin:12px 0 20px}
</style>''', unsafe_allow_html=True)

# 아래 여섯 건은 실제 채용공고가 아닌 시연용 가상 데이터입니다.
JOBS = [
    ('농산물 품질관리 보조','우성면',36.482,127.093,'품질관리','주간','월 230만원','제조업, 품질, 검사','농산물 선별·검수 및 현장 품질관리'),
    ('문화관광 안내 지원','웅진동',36.458,127.119,'관광·서비스','파트타임','시급 12,000원','안내, 고객응대, 교육','방문객 안내 및 관광 정보 제공'),
    ('지역 물류 현장 지원','신관동',36.471,127.136,'물류·관리','주간','월 220만원','물류, 운전, 관리','입출고 및 재고 관리 보조'),
    ('공공시설 환경관리','금성동',36.460,127.112,'공공·시설','오전','시급 11,500원','시설, 관리, 청소','시설 정리 및 환경 관리'),
    ('로컬푸드 매장 운영','반포면',36.398,127.244,'판매·서비스','파트타임','시급 12,500원','판매, 고객응대, 농업','매장 운영 및 상품 진열'),
    ('지역 돌봄 활동 지원','유구읍',36.552,126.951,'돌봄·교육','오전','시급 13,000원','돌봄, 교육, 상담','지역 돌봄 프로그램 운영 보조'),
]
COLS = ['직무','지역','위도','경도','분야','근무형태','보수','관련경력','설명']


def example_jobs():
    return pd.DataFrame(JOBS, columns=COLS).assign(출처='가상 예시', 공고링크='')


@st.cache_data(ttl=3600)
def load_jobs():
    path = Path(__file__).resolve().parent / 'data' / 'gongju_jobs.csv'
    if not path.is_file():
        return example_jobs()
    try:
        try:
            data = pd.read_csv(path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            data = pd.read_csv(path, encoding='cp949')
        if any(col not in data.columns for col in COLS):
            return example_jobs()
        data['위도'] = pd.to_numeric(data['위도'], errors='coerce')
        data['경도'] = pd.to_numeric(data['경도'], errors='coerce')
        data = data.dropna(subset=['직무','위도','경도']).copy()
        data = data[data['위도'].between(36.1,36.8) & data['경도'].between(126.7,127.5)].copy()
        if '출처' not in data.columns:
            data['출처'] = '출처 미확인'
        if '공고링크' not in data.columns:
            data['공고링크'] = ''
        for col in ['직무','지역','분야','근무형태','보수','관련경력','설명','출처','공고링크']:
            data[col] = data[col].fillna('').astype(str)
        return data
    except (OSError, ValueError, pd.errors.ParserError):
        return example_jobs()


def get_api_url():
    try:
        configured = st.secrets.get('NEXTWORK_API_URL', '')
        if configured:
            return str(configured).strip().rstrip('/')
    except (FileNotFoundError, KeyError, OSError):
        pass
    return os.environ.get('NEXTWORK_API_URL', 'http://127.0.0.1:8002').strip().rstrip('/')


def escape(value):
    return html.escape(str(value), quote=True)


df = load_jobs()
api_url = get_api_url()

with st.sidebar:
    st.markdown('## ✦ NEXTWORK')
    st.caption('공주의 경험을 새로운 기회로')
    st.divider()
    st.markdown('### 🔎 나에게 맞는 일자리')
    keyword = st.text_input('검색어', placeholder='예: 품질관리, 관광, 돌봄')
    experience = st.text_input('이전 경력', placeholder='예: 제조업 품질검사 20년')
    region = st.selectbox('희망 지역', ['공주시 전체'] + sorted(df['지역'].unique().tolist()))
    field = st.selectbox('희망 분야', ['전체'] + sorted(df['분야'].unique().tolist()))
    work = st.selectbox('근무 형태', ['전체'] + sorted(df['근무형태'].unique().tolist()))
    min_score = st.slider('추천 기준 점수', 0, 100, 60, 5)
    run_recommend = st.button('✨ 맞춤형 일자리 추천', type='primary', use_container_width=True)
    st.divider()
    st.caption('공주시에서 새로운 기회를 찾아보세요.')

# HTML을 반드시 한 줄 문자열로 전달해 Markdown의 코드 블록 변환을 방지합니다.
st.markdown('<div class="hero"><div class="eyebrow">GONGJU · CAREER REDISCOVERY PLATFORM</div><h1>경험은 끝나지 않습니다.<br>다음 기회가 시작됩니다.</h1><p>공주시 중장년·시니어를 위한 새로운 일자리 탐색 지도<br>익숙한 경력에서 새로운 가능성을 발견하세요.</p></div>', unsafe_allow_html=True)

if run_recommend:
    try:
        with st.spinner('NEXTWORK 추천 API에서 적합도를 계산하는 중입니다...'):
            response = requests.post(
                api_url + '/recommend',
                json={
                    'previous_job': experience,
                    'preferred_region': region if region != '공주시 전체' else '공주시',
                    'desired_job': field if field != '전체' else keyword,
                    'work_type': work if work != '전체' else '',
                    'min_score': min_score,
                    'limit': 50,
                },
                timeout=90,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get('status') != 'ok':
                raise ValueError('API 응답 형식 또는 상태가 올바르지 않습니다.')
            st.session_state['recommend_result'] = payload
            st.session_state['recommend_filters'] = (experience, region, field, work, keyword, min_score)
    except (requests.RequestException, ValueError) as exc:
        st.session_state.pop('recommend_result', None)
        st.session_state.pop('recommend_filters', None)
        st.error(f'추천 API 연결 실패: {exc}. API 서버와 NEXTWORK_API_URL 설정을 확인하세요.')

filtered = df.copy()
if 'recommend_result' in st.session_state:
    result = st.session_state['recommend_result']
    recommendations = result.get('recommendations', [])
    score_map = {(str(item.get('job')), str(item.get('region'))): item for item in recommendations}
    filtered = filtered[filtered.apply(lambda row: (str(row['직무']), str(row['지역'])) in score_map, axis=1)].copy()
    if not filtered.empty:
        filtered['적합도'] = filtered.apply(lambda row: score_map[(str(row['직무']), str(row['지역']))].get('score', 0), axis=1)
        filtered['거리_km'] = filtered.apply(lambda row: score_map[(str(row['직무']), str(row['지역']))].get('distance_km', '-'), axis=1)
        filtered['추천근거'] = filtered.apply(lambda row: score_map[(str(row['직무']), str(row['지역']))].get('reason', ''), axis=1)
        filtered = filtered.sort_values('적합도', ascending=False)
    st.success(f'API 호출 성공 · HTTP 200 · 전체 {result.get("total_candidates", 0)}건 중 {result.get("matched_count", 0)}건 추천 기준 통과')
    st.caption('추천 점수는 NEXTWORK 자체 API가 계산합니다. 추천 데이터의 실제 채용 여부는 별도로 확인해야 합니다.')
else:
    if keyword:
        search_text = filtered[['직무','분야','설명','관련경력']].astype(str).agg(' '.join, axis=1)
        filtered = filtered[search_text.str.contains(keyword, case=False, regex=False)]
    if region != '공주시 전체':
        filtered = filtered[filtered['지역'] == region]
    if field != '전체':
        filtered = filtered[filtered['분야'] == field]
    if work != '전체':
        filtered = filtered[filtered['근무형태'] == work]

k1, k2, k3, k4 = st.columns(4)
for column, label, value in [
    (k1, '탐색 중인 기회', f'{len(filtered)}개'),
    (k2, '일자리 분야', f'{filtered["분야"].nunique()}개'),
    (k3, '탐색 지역', f'{filtered["지역"].nunique()}곳'),
    (k4, '추천 방식', '자체 API' if 'recommend_result' in st.session_state else '일반 탐색'),
]:
    with column:
        st.markdown(f'<div class="kpi"><div class="label">{escape(label)}</div><div class="num">{escape(value)}</div></div>', unsafe_allow_html=True)

if (df['출처'] == '가상 예시').all():
    st.markdown('<div class="note">⚠️ 해커톤 프로토타입: 아래 일자리·급여·위치는 가상 예시이며, 실제 채용공고가 아닙니다.</div>', unsafe_allow_html=True)
else:
    st.info('일자리 데이터가 표시됩니다. 지원 전 모집 여부를 원문에서 확인하세요.')

map_tab, analysis_tab = st.tabs(['🗺️ 일자리 탐색 지도', '📊 데이터 인사이트'])
with map_tab:
    left, right = st.columns([1.45, 1], gap='large')
    with left:
        st.subheader('공주시 기회 지도')
        map_view = folium.Map(location=[36.46, 127.12], zoom_start=11, tiles='OpenStreetMap', control_scale=True)
        for _, row in filtered.iterrows():
            popup = f'<b>{escape(row["직무"])}</b><br>지역: {escape(row["지역"])}<br>분야: {escape(row["분야"])}<br>보수: {escape(row["보수"])}'
            folium.Marker(
                location=[float(row['위도']), float(row['경도'])],
                tooltip=str(row['직무']),
                popup=folium.Popup(popup, max_width=300),
            ).add_to(map_view)
        st_folium(map_view, height=570, use_container_width=True, returned_objects=[])
    with right:
        st.subheader(f'발견한 일자리 · {len(filtered)}건')
        if filtered.empty:
            st.info('조건에 맞는 예시 일자리가 없습니다. 필터를 조정해 보세요.')
        for idx, row in filtered.iterrows():
            if '적합도' in filtered.columns:
                st.markdown(f'**🎯 적합도 {int(row["적합도"])}점 / 100점 · 거리 {escape(row["거리_km"])}km**')
                st.caption(str(row['추천근거']))
            # HTML을 단일 문자열로 생성해 카드가 코드 블록으로 렌더링되지 않게 합니다.
            card = (
                f'<div class="job"><span class="badge">{escape(row["분야"])}</span>'
                f'<div class="title">{escape(row["직무"])}</div>'
                f'<div class="meta">📍 공주시 {escape(row["지역"])} · 🕒 {escape(row["근무형태"])}'
                f'<br>💰 {escape(row["보수"])}<br>{escape(row["설명"])}'
                f'<br>출처: {escape(row["출처"])}</div></div>'
            )
            st.markdown(card, unsafe_allow_html=True)
            link = str(row['공고링크']).strip()
            if link.startswith(('https://', 'http://')):
                st.link_button('🔗 원문 공고 확인', link, key=f'job_{idx}')

with analysis_tab:
    st.subheader('일자리 분포')
    st.caption('아래 차트는 현재 불러온 데이터의 집계입니다. 가상 데이터일 경우 실제 공주시 통계가 아닙니다.')
    a, b = st.columns(2)
    with a:
        counts = df['분야'].value_counts().rename_axis('분야').reset_index(name='건수')
        fig = px.bar(counts, x='분야', y='건수', title='분야별 예시 일자리 수', color='건수', color_continuous_scale='Blues')
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with b:
        counts2 = df['근무형태'].value_counts().rename_axis('근무형태').reset_index(name='건수')
        fig2 = px.pie(counts2, names='근무형태', values='건수', title='근무 형태별 분포', hole=0.58, color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig2, use_container_width=True)
    st.caption('표시된 수치는 현재 제공 중인 일자리 데이터 기준입니다.')
