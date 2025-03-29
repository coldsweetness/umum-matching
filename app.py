import streamlit as st
import requests
import json

API_BASE = "https://umum-matching.onrender.com"
ADMIN_API_KEY = "supersecretkey"  # 필요 시 수정

st.title("엄대엄 팀 매칭 시스템")

# ✅ 플레이어 목록 불러오기
try:
    response = requests.get(f"{API_BASE}/players/")
    response.raise_for_status()
    players_data = response.json()
    players_list = [p["name"] for p in players_data]
except requests.exceptions.RequestException as e:
    st.error(f"플레이어 데이터를 불러올 수 없습니다: {e}")
    players_data = []
    players_list = []

# ✅ 플레이어 점수 출력
st.subheader("🏆 현재 플레이어 점수")
for player in players_data:
    st.markdown(f"**{player['name']}**: {player['ratings']}")

# ✅ 🔹 플레이어 선택 및 팀 생성
selected_players = st.multiselect("🔹 10명의 플레이어를 선택하세요", players_list)

if st.button("팀 생성"):
    if len(selected_players) != 10:
        st.error("정확히 10명을 선택해야 합니다!")
    else:
        try:
            response = requests.post(f"{API_BASE}/matchmaking/", json={"selected_names": selected_players})
            response.raise_for_status()
            st.session_state["results"] = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 실패: {e}")

# ✅ 🔄 팀 결과 선택 및 경기 반영
if "results" in st.session_state:
    st.subheader("🔁 팀 매칭 결과")
    match_options = [f"매칭 {i+1}" for i in range(len(st.session_state["results"]))]
    selected_match = st.selectbox("사용할 매칭을 선택하세요", match_options)
    index = int(selected_match.split(" ")[1]) - 1
    match = st.session_state["results"][index]
    st.json(match)

    winner = st.radio("🏆 승리한 팀을 선택하세요", ["팀 1", "팀 2"])
    if st.button("경기 결과 반영"):
        match_result = {
            "winning_team": match["team1"] if winner == "팀 1" else match["team2"],
            "losing_team": match["team2"] if winner == "팀 1" else match["team1"]
        }
        try:
            response = requests.post(f"{API_BASE}/update_scores/", json=match_result)
            response.raise_for_status()
            st.success("경기 결과가 반영되었습니다!")
            del st.session_state["results"]
            st.experimental_rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"결과 반영 실패: {e}")

# =======================================
# ✅ 사이드바: 추가 기능들 (백업/복원/추가/삭제)
# =======================================

with st.sidebar:
    st.subheader("📦 플레이어 백업 및 복원")

    # ✅ 백업 다운로드
    if st.button("💾 JSON 백업 다운로드"):
        backup_data = json.dumps(players_data, indent=2, ensure_ascii=False)
        st.download_button("📥 백업 파일 저장", data=backup_data, file_name="players_backup.json", mime="application/json")

    # ✅ 복원 업로드
    upload = st.file_uploader("📤 백업 파일 업로드", type="json")
    if upload is not None:
        try:
            uploaded_players = json.load(upload)
            for p in uploaded_players:
                requests.post(f"{API_BASE}/add_player/", json=p)
            st.success("✅ 복원 완료! 새로고침하세요.")
        except Exception as e:
            st.error(f"복원 실패: {e}")

    # ✅ 새 플레이어 추가
    st.subheader("➕ 새 플레이어 추가")
    new_name = st.text_input("이름")
    new_ratings = {
        "top": st.number_input("Top", 0, 100, 50),
        "jungle": st.number_input("Jungle", 0, 100, 50),
        "mid": st.number_input("Mid", 0, 100, 50),
        "adc": st.number_input("ADC", 0, 100, 50),
        "support": st.number_input("Support", 0, 100, 50),
    }
    if st.button("추가"):
        res = requests.post(f"{API_BASE}/add_player/", json={"name": new_name, "ratings": new_ratings})
        if res.status_code == 200:
            st.success("플레이어 추가 완료! 새로고침하세요.")
        else:
            st.error("추가 실패")

    # ✅ 플레이어 삭제 (관리자용)
    st.subheader("🗑 플레이어 삭제")
    delete_name = st.selectbox("삭제할 이름", players_list)
    admin_key = st.text_input("관리자 키 입력", type="password")
    if st.button("삭제"):
        if admin_key != ADMIN_API_KEY:
            st.error("관리자 키가 일치하지 않습니다.")
        else:
            res = requests.delete(f"{API_BASE}/delete_player/{delete_name}", headers={"api_key": admin_key})
            if res.status_code == 200:
                st.success(f"{delete_name} 삭제 완료. 새로고침하세요.")
            else:
                st.error(f"삭제 실패: {res.json()}")
