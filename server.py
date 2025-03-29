# 기존 import 및 초기 설정은 그대로 유지
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import itertools
import sqlite3
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_API_KEY = "supersecretkey"
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

class Player(BaseModel):
    name: str
    ratings: Dict[str, int]

class TeamRequest(BaseModel):
    selected_names: List[str]

class MatchResult(BaseModel):
    winning_team: Dict[str, str]
    losing_team: Dict[str, str]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Umum Matching API!"}

@app.get("/players/")
def get_players():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    players = [{"name": row[0], "ratings": {
        "top": row[1], "jungle": row[2], "mid": row[3], "adc": row[4], "support": row[5]
    }} for row in cursor.fetchall()]
    conn.close()
    return players

@app.post("/add_player/")
def add_player(player: Player):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO players (name, top, jungle, mid, adc, support) VALUES (?, ?, ?, ?, ?, ?)",
                   (player.name, player.ratings["top"], player.ratings["jungle"],
                    player.ratings["mid"], player.ratings["adc"], player.ratings["support"]))
    conn.commit()
    conn.close()
    return {"message": "플레이어 추가 완료"}

@app.delete("/delete_player/{player_name}")
def delete_player(player_name: str, api_key: str = Header(None)):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="🚨 접근이 거부되었습니다. 관리자만 삭제할 수 있습니다.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE name = ?", (player_name,))
    player = cursor.fetchone()
    if not player:
        conn.close()
        return {"error": f"플레이어 '{player_name}'을 찾을 수 없습니다."}, 404
    cursor.execute("DELETE FROM players WHERE name = ?", (player_name,))
    conn.commit()
    conn.close()
    return {"message": f"플레이어 '{player_name}' 삭제 완료"}

# ✅ 수정된 매칭 API - 0점 포지션 배제
@app.post("/matchmaking/")
def find_top_balanced_lane_teams(request: TeamRequest):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE name IN ({seq})".format(
        seq=','.join(['?'] * len(request.selected_names))
    ), request.selected_names)
    selected_players = [{"name": row[0], "ratings": {
        "top": row[1], "jungle": row[2], "mid": row[3], "adc": row[4], "support": row[5]
    }} for row in cursor.fetchall()]
    conn.close()

    if len(selected_players) != 10:
        return {"error": "선택된 플레이어 수는 10명이 되어야 합니다."}

    lanes = ["top", "jungle", "mid", "adc", "support"]
    valid_assignments = []

    for team1 in itertools.combinations(selected_players, 5):
        team2 = [p for p in selected_players if p not in team1]

        for perm1 in itertools.permutations(team1):
            for perm2 in itertools.permutations(team2):
                # ✅ 포지션이 0점인 경우 배제
                valid = True
                for i, lane in enumerate(lanes):
                    if perm1[i]["ratings"][lane] == 0 or perm2[i]["ratings"][lane] == 0:
                        valid = False
                        break
                if not valid:
                    continue

                team1_score = sum(perm1[i]["ratings"][lane] for i, lane in enumerate(lanes))
                team2_score = sum(perm2[i]["ratings"][lane] for i, lane in enumerate(lanes))
                total_diff = abs(team1_score - team2_score)

                valid_assignments.append({
                    "team1": {lane: perm1[i]["name"] for i, lane in enumerate(lanes)},
                    "team2": {lane: perm2[i]["name"] for i, lane in enumerate(lanes)},
                    "total_diff": total_diff
                })

    valid_assignments.sort(key=lambda x: x["total_diff"])
    return valid_assignments[:10]

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

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT, lifespan="on")
