import streamlit as st
import requests

# ✅ FastAPI 서버 주소 (배포된 주소 사용)
API_BASE = "https://umum-matching.onrender.com"

st.title("엄대엄 팀 매칭 시스템")

# ✅ 플레이어 목록 불러오기
try:
    response = requests.get(f"{API_BASE}/players/")
    response.raise_for_status()
    players_list = [p["name"] for p in response.json()]
except requests.exceptions.RequestException as e:
    st.error(f"플레이어 데이터를 불러올 수 없습니다: {e}")
    players_list = []

# ✅ 플레이어 추가 기능 (사이드바)
with st.sidebar:
    st.subheader("📌 새 플레이어 추가")
    new_name = st.text_input("플레이어 이름")
    new_ratings = {
        "top": st.number_input("Top", 0, 100, 50),
        "jungle": st.number_input("Jungle", 0, 100, 50),
        "mid": st.number_input("Mid", 0, 100, 50),
        "adc": st.number_input("ADC", 0, 100, 50),
        "support": st.number_input("Support", 0, 100, 50),
    }
    if st.button("플레이어 추가"):
        try:
            res = requests.post(f"{API_BASE}/add_player/", json={"name": new_name, "ratings": new_ratings})
            res.raise_for_status()
            st.success("플레이어 추가 완료! 새로고침하세요.")
        except requests.exceptions.RequestException as e:
            st.error(f"플레이어 추가 실패: {e}")

# ✅ 플레이어 삭제 기능 (사이드바)
with st.sidebar:
    st.subheader("🗑 플레이어 삭제")
    if players_list:
        player_to_delete = st.selectbox("삭제할 플레이어 선택", players_list)
        if st.button("플레이어 삭제"):
            try:
                res = requests.delete(f"{API_BASE}/delete_player/{player_to_delete}")
                res.raise_for_status()
                st.success(f"플레이어 {player_to_delete} 삭제 완료! 새로고침하세요.")
            except requests.exceptions.RequestException as e:
                st.error(f"플레이어 삭제 실패: {e}")

# ✅ 10명 선택 UI
selected_players = st.multiselect("🔹 10명의 플레이어를 선택하세요", players_list)

if st.button("팀 생성"):
    if len(selected_players) != 10:
        st.error("정확히 10명을 선택해야 합니다!")
    else:
        try:
            response = requests.post(f"{API_BASE}/matchmaking/", json={"selected_names": selected_players})
            response.raise_for_status()
            results = response.json()
            st.session_state["results"] = results
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 실패: {e}")

# ✅ 생성된 팀 조합 중 하나 선택 & 경기 결과 입력
if "results" in st.session_state:
    st.write("🔹 팀 배정 결과:")
    match_options = [f"매칭 {i+1}" for i in range(len(st.session_state["results"]))]
    selected_match = st.selectbox("사용할 팀 매칭을 선택하세요", options=match_options)

    if selected_match:
        match_index = int(selected_match.split(" ")[1]) - 1
        chosen_match = st.session_state["results"][match_index]
        st.json(chosen_match)

        # ✅ 경기 결과 입력
        st.subheader("🏆 경기 결과 입력")
        winning_team = st.radio("승리한 팀을 선택하세요", ["팀 1", "팀 2"])
        
        if st.button("경기 결과 반영"):
            match_result = {
                "winning_team": chosen_match["team1"] if winning_team == "팀 1" else chosen_match["team2"],
                "losing_team": chosen_match["team2"] if winning_team == "팀 1" else chosen_match["team1"]
            }
            try:
                res = requests.post(f"{API_BASE}/update_scores/", json=match_result)
                res.raise_for_status()
                st.success("경기 결과 반영 완료! 새로고침하세요.")
                del st.session_state["results"]  # 경기 결과 반영 후 초기화
            except requests.exceptions.RequestException as e:
                st.error(f"결과 반영 실패: {e}")
