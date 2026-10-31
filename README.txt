NEXTWORK WEB + API integrated

1) Terminal A:
cd api
python -m pip install -r requirements.txt
python -m uvicorn recommend_api:app --host 127.0.0.1 --port 8002

2) Terminal B (from project root):
cd web
python -m pip install -r requirements.txt
python -m streamlit run app.py

3) In Streamlit sidebar select conditions and click 맞춤형 일자리 추천. The web sends real HTTP POST /recommend to the API. If API is offline the button fails; no fabricated success.

Deployment: deploy api/ to Render with Root Directory api, then set NEXTWORK_API_URL environment variable on Streamlit web host to your public https://...onrender.com API base URL. Deploy web/ on Streamlit Community Cloud with Main file path web/app.py. Add requests in web/requirements.txt.

WARNING: The included 48 jobs are SYNTHETIC DEMO listings, not real vacancies.
