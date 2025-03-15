from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import itertools
import sqlite3
import uvicorn
import os

app = FastAPI()

# ✅ CORS 설정 (Streamlit과 연동을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (보안 필요시 특정 도메인만 허용 가능)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ SQLite 데이터베이스 설정
DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            name TEXT PRIMARY KEY,
            top INTEGER DEFAULT 50,
            jungle INTEGER DEFAULT 50,
            mid INTEGER DEFAULT 50,
            adc INTEGER DEFAULT 50,
            support INTEGER DEFAULT 50
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ✅ 데이터 모델 정의
class Player(BaseModel):
    name: str
    ratings: Dict[str, int]

class TeamRequest(BaseModel):
    selected_names: List[str]

class MatchResult(BaseModel):
    winning_team: Dict[str, str]
    losing_team: Dict[str, str]

# ✅ 기본 엔드포인트
@app.get("/")
def read_root():
    return {"message": "Welcome to the Umum Matching API!"}

# ✅ 모든 플레이어 목록 반환
@app.get("/players/")
def get_players():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    players = [{"name": row[0], "ratings": {"top": row[1], "jungle": row[2], "mid": row[3], "adc": row[4], "support": row[5]}} for row in cursor.fetchall()]
    conn.close()
    return players

# ✅ 새 플레이어 추가
@app.post("/add_player/")
def add_player(player: Player):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO players (name, top, jungle, mid, adc, support) VALUES (?, ?, ?, ?, ?, ?)",
                   (player.name, player.ratings["top"], player.ratings["jungle"], player.ratings["mid"], player.ratings["adc"], player.ratings["support"]))
    conn.commit()
    conn.close()
    return {"message": "플레이어 추가 완료"}

# ✅ 플레이어 삭제
@app.delete("/delete_player/{player_name}")
def delete_player(player_name: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # ✅ 플레이어 존재 여부 확인
    cursor.execute("SELECT * FROM players WHERE name = ?", (player_name,))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        return {"error": f"플레이어 '{player_name}'을 찾을 수 없습니다."}, 404
    
    # ✅ 플레이어 삭제 수행
    cursor.execute("DELETE FROM players WHERE name = ?", (player_name,))
    conn.commit()
    conn.close()
    
    return {"message": f"플레이어 '{player_name}' 삭제 완료"}


# ✅ 팀 매칭 (최적 10개 조합 반환)
@app.post("/matchmaking/")
def find_top_balanced_lane_teams(request: TeamRequest):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE name IN ({seq})".format(
        seq=','.join(['?'] * len(request.selected_names))
    ), request.selected_names)
    selected_players = [{"name": row[0], "ratings": {"top": row[1], "jungle": row[2], "mid": row[3], "adc": row[4], "support": row[5]}} for row in cursor.fetchall()]
    conn.close()

    if len(selected_players) != 10:
        return {"error": "선택된 플레이어 수는 10명이 되어야 합니다."}

    lanes = ["top", "jungle", "mid", "adc", "support"]
    valid_assignments = []
    for team1 in itertools.combinations(selected_players, 5):
        team2 = [p for p in selected_players if p not in team1]
        valid_assignments.append({
            "team1": {lane: team1[i]["name"] for i, lane in enumerate(lanes)},
            "team2": {lane: team2[i]["name"] for i, lane in enumerate(lanes)},
        })

    return valid_assignments[:10]  # 최대 10개 반환

# ✅ 경기 결과 반영
@app.post("/update_scores/")
def update_scores(result: MatchResult):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for lane, winner in result.winning_team.items():
        cursor.execute(f"UPDATE players SET {lane} = {lane} + 1 WHERE name = ?", (winner,))
    
    for lane, loser in result.losing_team.items():
        cursor.execute(f"UPDATE players SET {lane} = MAX(0, {lane} - 1) WHERE name = ?", (loser,))
    
    conn.commit()
    conn.close()
    return {"message": "점수 업데이트 완료"}

# ✅ FastAPI 실행
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT, lifespan="on")
