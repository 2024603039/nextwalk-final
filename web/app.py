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
