import streamlit as st
import requests

API_BASE = "https://umum-matching.onrender.com"

st.title("엄대엄 팀 매칭 시스템")

response = requests.get(f"{API_BASE}/players/")
players_list = [p["name"] for p in response.json()]

selected_players = st.multiselect("🔹 10명의 플레이어를 선택하세요", players_list)

if st.button("팀 생성"):
    if len(selected_players) != 10:
        st.error("정확히 10명을 선택해야 합니다!")
    else:
        response = requests.post(f"{API_BASE}/matchmaking/", json={"selected_names": selected_players})
        results = response.json()
        st.session_state["results"] = results

if "results" in st.session_state:
    st.write("🔹 팀 배정 결과 (최대 10개 중 선택):")
    selected_match = st.selectbox("사용할 팀 매칭을 선택하세요", options=[f"매칭 {i+1}" for i in range(len(st.session_state["results"]))])
    match_index = int(selected_match.split(" ")[1]) - 1
    chosen_match = st.session_state["results"][match_index]
    
    st.json(chosen_match)

    winning_team = st.radio("어느 팀이 승리했나요?", ["팀 1", "팀 2"])
    
    if st.button("승패 반영 및 업데이트"):
        match_result = {
            "winning_team": chosen_match["team1"] if winning_team == "팀 1" else chosen_match["team2"],
            "losing_team": chosen_match["team2"] if winning_team == "팀 1" else chosen_match["team1"]
        }
        requests.post(f"{API_BASE}/update_scores/", json=match_result)
        st.success("점수 업데이트 완료!")
