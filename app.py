import streamlit as st
import requests

# ✅ FastAPI 서버가 로컬에서 실행 중일 때
API_BASE = "http://127.0.0.1:8000"

st.title("엄대엄 팀 매칭 시스템")

# ✅ 플레이어 목록 불러오기
try:
    response = requests.get(f"{API_BASE}/players/")
    response.raise_for_status()
    players_list = [p["name"] for p in response.json()]
except requests.exceptions.RequestException as e:
    st.error(f"플레이어 데이터를 불러올 수 없습니다: {e}")
    players_list = []

# ✅ 플레이어 추가 기능
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

# ✅ 결과 표시
if "results" in st.session_state:
    st.write("🔹 팀 배정 결과:")
    st.json(st.session_state["results"])
