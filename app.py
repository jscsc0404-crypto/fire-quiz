import json
import math
from datetime import datetime, timedelta
from google import genai
import streamlit as st

# 1. 화면 최적화 설정
st.set_page_config(
    page_title="소방시설관리사 2차 AI 암기노트",
    page_icon="🚒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .main { padding: 1rem; }
    stButton > button { width: 100%; height: 3.5rem; font-size: 1.2rem !important; border-radius: 12px; font-weight: bold; }
    .stTextArea textarea { font-size: 1.1rem !important; line-height: 1.5; }
    .card-box { background-color: #f8f9fa; border-radius: 12px; padding: 18px; margin-bottom: 15px; border-left: 5px solid #ff4b4b; }
    .score-badge { font-size: 1.4rem; font-weight: bold; color: #1e88e5; }
</style>
""",
    unsafe_allow_html=True,
)

# 2. Gemini API 키 입력
st.sidebar.title("⚙️ 설정")
api_key = st.sidebar.text_input(
    "Google Gemini API Key를 입력하세요", type="password"
)

# 3. 데이터 및 상태 초기화
if "cards" not in st.session_state:
  st.session_state.cards = [
      {
          "id": 1,
          "question": (
              "화재안전성능기준(FPC)에 따른 자동화재탐지설비의 감지기 설치제외"
              " 장소 4가지를 쓰시오."
          ),
          "standard_answers": [
              "천장 또는 반자의 높이가 20m 이상인 장소",
              "부식성 가스가 체류하는 장소",
              "고온도 및 저온도로서 감지기의 기능이 상실되기 쉬운 장소",
              "목욕실·욕조나 샤워시설이 있는 부스·변기설비가 있는 장소",
          ],
          "total_score": 4,
          "interval": 1,
          "ease_factor": 2.5,
          "repetitions": 0,
          "next_review": datetime.now().isoformat(),
      },
      {
          "id": 2,
          "question": (
              "옥내소화전설비의 가압송수장치 릴리프밸브 체절압력 관련 점검항목"
              " 2가지를 쓰시오."
          ),
          "standard_answers": [
              (
                  "체절운전 시 체절압력 이하에서 릴리프밸브가 작동하는지"
                  " 여부"
              ),
              "정격부하 운전 시 체절압력의 140%를 초과하지 않는지 여부",
          ],
          "total_score": 2,
          "interval": 1,
          "ease_factor": 2.5,
          "repetitions": 0,
          "next_review": datetime.now().isoformat(),
      },
  ]

if "last_result" not in st.session_state:
  st.session_state.last_result = None


# 4. Anki 알고리즘
def update_anki_schedule(card, score, max_score):
  ratio = score / max_score if max_score > 0 else 0
  quality = math.floor(ratio * 5)

  interval = card["interval"]
  ease_factor = card["ease_factor"]
  repetitions = card["repetitions"]

  if quality >= 3:
    if repetitions == 0:
      interval = 1
    elif repetitions == 1:
      interval = 3
    else:
      interval = math.ceil(interval * ease_factor)
    repetitions += 1
  else:
    repetitions = 0
    interval = 1

  ease_factor = max(
      1.3,
      ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
  )
  card["interval"] = interval
  card["ease_factor"] = ease_factor
  card["repetitions"] = repetitions
  card["next_review"] = (datetime.now() + timedelta(days=interval)).isoformat()


# 5. 최신 모델 적용 채점 함수
def ai_grade_answer(
    question, standard_answers, total_score, user_answer, api_key
):
  if not api_key:
    return {
        "error": (
            "Gemini API Key가 설정되지 않았습니다. 사이드바에 키를"
            " 입력하세요."
        )
    }

  try:
    client = genai.Client(api_key=api_key)

    prompt = f"""
너는 소방시설관리사 2차 채점관이다. 수험생 답안을 검토하여 정답 여부와 부분 점수를 판정하라.

[문제]: {question}
[출제자 모범답안 목록 ({len(standard_answers)}개 항목, 총 배점 {total_score}점)]:
{json.dumps(standard_answers, ensure_ascii=False, indent=2)}

[수험생 작성 답안]:
{user_answer}

[채점 규칙]:
1. 의미가 일치하면 정답 인정하라.
2. 각 항목의 배점은 (총점 / 항목수) 이다.
3. 반드시 오직 JSON 형식으로만 반환하라. 순수 JSON 텍스트 외에 다른 설명은 넣지 마라:
{{
    "earned_score": 획득점수(숫자),
    "total_score": 총배점(숫자),
    "detailed_feedback": "총평 및 설명",
    "item_results": [
        {{
            "standard_item": "모범답안 항목",
            "is_correct": true 또는 false,
            "user_matched_text": "수험생이 쓴 관련 문구",
            "comment": "이유"
        }}
    ]
}}
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)
  except Exception as e:
    return {"error": f"API 오류: {str(e)}"}


# 6. 화면 구성
st.title("🚒 소방시설관리사 2차 AI 암기노트")

st.session_state.cards.sort(key=lambda x: x["next_review"])
current_card = st.session_state.cards[0]

st.markdown(
    f"""
<div class="card-box">
    <h3 style="margin:0; color:#d32f2f;">Q. {current_card['question']}</h3>
    <p style="margin-top:8px; color:#555; font-size:0.95rem;"><b>총 배점:</b> {current_card['total_score']}점 | <b>복습 주기:</b> {current_card['interval']}일 후</p>
</div>
""",
    unsafe_allow_html=True,
)

user_input = st.text_area(
    "✍️ 답안 작성", height=150, placeholder="1. ...\n2. ..."
)

if st.button("🤖 AI 채점하기", type="primary"):
  if not user_input.strip():
    st.warning("답안을 입력해주세요.")
  else:
    with st.spinner("AI가 채점 중입니다..."):
      result = ai_grade_answer(
          current_card["question"],
          current_card["standard_answers"],
          current_card["total_score"],
          user_input,
          api_key,
      )
      if "error" in result:
        st.error(result["error"])
      else:
        st.session_state.last_result = result
        update_anki_schedule(
            current_card, result["earned_score"], result["total_score"]
        )

if (
    st.session_state.last_result
    and "earned_score" in st.session_state.last_result
):
  res = st.session_state.last_result
  st.markdown("---")
  st.subheader("📊 AI 채점 결과")
  st.markdown(
      f"<p class='score-badge'>획득 점수: {res['earned_score']} /"
      f" {res['total_score']} 점</p>",
      unsafe_allow_html=True,
  )
  st.info(f"**총평:** {res.get('detailed_feedback', '')}")

  for item in res.get("item_results", []):
    icon = "✅" if item["is_correct"] else "❌"
    with st.expander(f"{icon} {item['standard_item']}"):
      st.write(f"- **작성한 내용:** {item.get('user_matched_text') or '누락'}")
      st.write(f"- **채점 의견:** {item.get('comment')}")

  if st.button("다음 문제 풀기 ➡️"):
    st.session_state.last_result = None
    st.rerun()
