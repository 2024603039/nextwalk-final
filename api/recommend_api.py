from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from recommender import recommend_jobs

app=FastAPI(title='NEXTWORK Recommendation API',version='2.0.0')
class Profile(BaseModel):
    previous_job: str = ''
    experience_years: int = Field(0,ge=0,le=80)
    preferred_region: str = '신관동'
    desired_job: str = ''
    preferred_category: str = ''
    work_type: str = ''
    latitude: float | None = Field(None,ge=-90,le=90)
    longitude: float | None = Field(None,ge=-180,le=180)
    min_score: int = Field(60,ge=0,le=100)
    limit: int = Field(5,ge=1,le=50)

@app.get('/')
@app.get('/health')
def health():
    return {'status':'ok','service':'NEXTWORK Recommendation API','message':'호출 성공','version':'2.0.0'}

@app.post('/recommend')
def recommend(profile:Profile):
    try: return recommend_jobs(**profile.model_dump())
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e))
