import os
import json
import itertools
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# ✅ 데이터 저장 파일
DATA_FILE = "players_data.json"

# ✅ 데이터 로드 (없으면 빈 리스트)
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        players_pool = json.load(f)
else:
    players_pool = []

# ✅ 데이터 저장 함수 (파일 저장 후 실시간 반영)
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players_pool, f, ensure_ascii=False, indent=4)
    # 저장 후 다시 불러와 반영
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        global players_pool
        players_pool = json.load(f)

# ✅ 요청 데이터 모델
class Player(BaseModel):
    name: str
    ratings: Dict[str, int]

class TeamRequest(BaseModel):
    selected_names: List[str]

class MatchResult(BaseModel):
    winning_team: Dict[str, str]
    losing_team: Dict[str, str]

# ✅ 기본 루트 엔드포인트 추가
@app.get("/")
def read_root():
    return {"message": "Welcome to the Umum Matching API!"}

# ✅ 모든 플레이어 목록 반환 API
@app.get("/players/")
def get_players():
    return players_pool

# ✅ 새 플레이어 추가 API
@app.post("/add_player/")
def add_player(player: Player):
    for p in players_pool:
        if p["name"] == player.name:
            return {"error": "이미 존재하는 플레이어입니다."}
    
    players_pool.append({"name": player.name, "ratings": player.ratings})
    save_data()
    return {"message": "플레이어 추가 완료"}

# ✅ 팀 배정 API
@app.post("/matchmaking/")
def find_top_balanced_lane_teams(request: TeamRequest):
    selected_players = [p for p in players_pool if p["name"] in request.selected_names]
    if len(selected_players) != 10:
        return {"error": "선택된 플레이어 수는 10명이 되어야 합니다."}

    lanes = ["top", "jungle", "mid", "adc", "support"]
    valid_assignments = []
    lane_weights = {'top': 20, 'jungle': 23, 'mid': 24, 'adc': 18, 'support': 15}

    for team1 in itertools.combinations(selected_players, 5):
        team2 = [p for p in selected_players if p not in team1]
        for perm1 in itertools.permutations(team1):
            for perm2 in itertools.permutations(team2):
                total_team_diff = abs(sum(p["ratings"][lane] for lane, p in zip(lanes, perm1)) - 
                                      sum(p["ratings"][lane] for lane, p in zip(lanes, perm2)))
                total_diff = sum(abs(p1["ratings"][lane] - p2["ratings"][lane]) * (lane_weights[lane] / 100)
                                 for lane, p1, p2 in zip(lanes, perm1, perm2)
                                 if p1["ratings"][lane] > 0 and p2["ratings"][lane] > 0)
                
                valid_assignments.append({
                    "team1": {lane: p1["name"] for lane, p1 in zip(lanes, perm1)},
                    "team2": {lane: p2["name"] for lane, p2 in zip(lanes, perm2)},
                    "total_team_diff": total_team_diff,
                    "weighted_total_diff": total_diff
                })

    valid_assignments.sort(key=lambda x: x["weighted_total_diff"])
    return valid_assignments[:20]

# ✅ 경기 결과 반영 API (이긴 팀 `+1`, 진 팀 `-1`)
@app.post("/update_scores/")
def update_scores(result: MatchResult):
    for lane, winner in result.winning_team.items():
        for p in players_pool:
            if p["name"] == winner:
                p["ratings"][lane] += 1  

    for lane, loser in result.losing_team.items():
        for p in players_pool:
            if p["name"] == loser:
                p["ratings"][lane] = max(0, p["ratings"][lane] - 1)  

    save_data()
    return {"message": "점수 업데이트 완료"}

# ✅ 기존 플레이어 삭제 API
@app.delete("/delete_player/{player_name}")
def delete_player(player_name: str):
    global players_pool
    new_players = [p for p in players_pool if p["name"] != player_name]
    
    if len(new_players) == len(players_pool):
        return {"error": "존재하지 않는 플레이어입니다."}

    players_pool = new_players
    save_data()
    return {"message": f"플레이어 '{player_name}' 삭제 완료"}

# ✅ Render 환경변수에 맞춰 실행 (PORT 설정)
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
