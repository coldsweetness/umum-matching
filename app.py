import streamlit as st
import requests

# ✅ FastAPI 서버 주소 업데이트 (배포된 주소 사용)
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

if "results" in st.session_state:
    st.write("🔹 팀 배정 결과:")
    st.json(st.session_state["results"])
