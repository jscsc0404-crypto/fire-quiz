import json

import math

from datetime import datetime, timedelta

import openai

import streamlit as st



\# --- 1. 아이패드 / 아이폰 화면 최적화 설정 ---

st.set\_page\_config(

&#x20;   page\_title="소방시설관리사 2차 AI 암기노트",

&#x20;   page\_icon="🚒",

&#x20;   layout="centered",

&#x20;   initial\_sidebar\_state="collapsed",

)



\# 모바일 UI 스타일링 (대형 버튼, 가독성 높은 폰트)

st.markdown(

&#x20;   """

<style>

&#x20;   .main { padding: 1rem; }

&#x20;   stButton > button { width: 100%; height: 3.5rem; font-size: 1.2rem !important; border-radius: 12px; font-weight: bold; }

&#x20;   .stTextArea textarea { font-size: 1.1rem !important; line-height: 1.5; }

&#x20;   .card-box { background-color: #f8f9fa; border-radius: 12px; padding: 18px; margin-bottom: 15px; border-left: 5px solid #ff4b4b; }

&#x20;   .score-badge { font-size: 1.4rem; font-weight: bold; color: #1e88e5; }

</style>

""",

&#x20;   unsafe\_allow\_html=True,

)



\# --- 2. OpenAI API 키 설정 ---

st.sidebar.title("⚙️ 설정")

api\_key = st.sidebar.text\_input("OpenAI API Key를 입력하세요", type="password")



\# --- 3. 문제 DB 및 Anki 상태 관리 ---

if "cards" not in st.session\_state:

&#x20; st.session\_state.cards = \[

&#x20;     {

&#x20;         "id": 1,

&#x20;         "question": (

&#x20;             "화재안전성능기준(FPC)에 따른 자동화재탐지설비의 감지기 설치제외"

&#x20;             " 장소 4가지를 쓰시오."

&#x20;         ),

&#x20;         "standard\_answers": \[

&#x20;             "천장 또는 반자의 높이가 20m 이상인 장소",

&#x20;             "부식성 가스가 체류하는 장소",

&#x20;             "고온도 및 저온도로서 감지기의 기능이 상실되기 쉬운 장소",

&#x20;             "목욕실·욕조나 샤워시설이 있는 부스·변기설비가 있는 장소",

&#x20;         ],

&#x20;         "total\_score": 4,

&#x20;         "interval": 1,

&#x20;         "ease\_factor": 2.5,

&#x20;         "repetitions": 0,

&#x20;         "next\_review": datetime.now().isoformat(),

&#x20;     },

&#x20;     {

&#x20;         "id": 2,

&#x20;         "question": (

&#x20;             "옥내소화전설비의 가압송수장치 릴리프밸브 체절압력 관련 점검항목"

&#x20;             " 2가지를 쓰시오."

&#x20;         ),

&#x20;         "standard\_answers": \[

&#x20;             (

&#x20;                 "체절운전 시 체절압력 이하에서 릴리프밸브가 작동하는지"

&#x20;                 " 여부"

&#x20;             ),

&#x20;             "정격부하 운전 시 체절압력의 140%를 초과하지 않는지 여부",

&#x20;         ],

&#x20;         "total\_score": 2,

&#x20;         "interval": 1,

&#x20;         "ease\_factor": 2.5,

&#x20;         "repetitions": 0,

&#x20;         "next\_review": datetime.now().isoformat(),

&#x20;     },

&#x20; ]



if "last\_result" not in st.session\_state:

&#x20; st.session\_state.last\_result = None





\# --- 4. Anki SM-2 간격 반복 알고리즘 ---

def update\_anki\_schedule(card, score, max\_score):

&#x20; ratio = score / max\_score if max\_score > 0 else 0

&#x20; quality = math.floor(ratio \* 5)  # 0\~5 등급 변환



&#x20; interval = card\["interval"]

&#x20; ease\_factor = card\["ease\_factor"]

&#x20; repetitions = card\["repetitions"]



&#x20; if quality >= 3:

&#x20;   if repetitions == 0:

&#x20;     interval = 1

&#x20;   elif repetitions == 1:

&#x20;     interval = 3

&#x20;   else:

&#x20;     interval = math.ceil(interval \* ease\_factor)

&#x20;   repetitions += 1

&#x20; else:

&#x20;   repetitions = 0

&#x20;   interval = 1



&#x20; ease\_factor = max(

&#x20;     1.3,

&#x20;     ease\_factor + (0.1 - (5 - quality) \* (0.08 + (5 - quality) \* 0.02)),

&#x20; )

&#x20; next\_review = (datetime.now() + timedelta(days=interval)).isoformat()



&#x20; card\["interval"] = interval

&#x20; card\["ease\_factor"] = ease\_factor

&#x20; card\["repetitions"] = repetitions

&#x20; card\["next\_review"] = next\_review





\# --- 5. GPT-4o-mini 기반 유연 채점 엔진 ---

def ai\_grade\_answer(

&#x20;   question, standard\_answers, total\_score, user\_answer, api\_key

):

&#x20; if not api\_key:

&#x20;   return {

&#x20;       "error": (

&#x20;           "OpenAI API Key가 설정되지 않았습니다. 사이드바에 키를"

&#x20;           " 입력하세요."

&#x20;       )

&#x20;   }



&#x20; client = openai.OpenAI(api\_key=api\_key)



&#x20; prompt = f"""

너는 소방시설관리사 2차 채점관이다. 수험생 답안을 검토하여 정답 여부와 부분 점수를 정확히 판정하라.



\[문제]: {question}

\[출제자 모범답안 목록 ({len(standard\_answers)}개 항목, 총 배점 {total\_score}점)]:

{json.dumps(standard\_answers, ensure\_ascii=False, indent=2)}



\[수험생 작성 답안]:

{user\_answer}



\[채점 규칙]:

1\. 조사, 핵심 단어 동의어, 문장 순서 변경 등 문맥상 의미가 일치하면 정답 인정하라.

2\. 각 모범답안 항목의 배점은 (총점 / 항목수) 이다. 일부만 맞고 일부가 틀렸다면 부분 점수를 부여하라.

3\. 결과를 JSON 형식으로만 반환하라:

{{

&#x20;   "earned\_score": 획득점수(숫자),

&#x20;   "total\_score": 총배점(숫자),

&#x20;   "detailed\_feedback": "감점 사유 및 총평 설명",

&#x20;   "item\_results": \[

&#x20;       {{

&#x20;           "standard\_item": "모범답안 항목",

&#x20;           "is\_correct": true 또는 false,

&#x20;           "user\_matched\_text": "수험생이 쓴 관련 문구",

&#x20;           "comment": "채점 판단 상세 이유"

&#x20;       }}

&#x20;   ]

}}

"""



&#x20; try:

&#x20;   response = client.chat.completions.create(

&#x20;       model="gpt-4o-mini",

&#x20;       messages=\[{"role": "user", "content": prompt}],

&#x20;       response\_format={"type": "json\_object"},

&#x20;   )

&#x20;   return json.loads(response.choices\[0].message.content)

&#x20; except Exception as e:

&#x20;   return {"error": f"API 호출 오류: {str(e)}"}





\# --- 6. 앱 UI 구성 ---

st.title("🚒 소방시설관리사 2차 AI 암기노트")



\# 복습 시기 및 오답 빈도가 높은 순으로 정렬

st.session\_state.cards.sort(key=lambda x: x\["next\_review"])

current\_card = st.session\_state.cards\[0]



\# 문제 카드 표시

st.markdown(

&#x20;   f"""

<div class="card-box">

&#x20;   <h3 style="margin:0; color:#d32f2f;">Q. {current\_card\['question']}</h3>

&#x20;   <p style="margin-top:8px; color:#555; font-size:0.95rem;"><b>총 배점:</b> {current\_card\['total\_score']}점 | <b>복습 주기:</b> {current\_card\['interval']}일 후 | <b>연속 정답:</b> {current\_card\['repetitions']}회</p>

</div>

""",

&#x20;   unsafe\_allow\_html=True,

)



\# 답안 입력창

user\_input = st.text\_area(

&#x20;   "✍️ 답안을 작성하세요 (아이패드 손글씨 변환/키보드 입력 가능)",

&#x20;   height=150,

&#x20;   placeholder="1. ...\\n2. ...\\n3. ...",

)



if st.button("🤖 AI 채점하기", type="primary"):

&#x20; if not user\_input.strip():

&#x20;   st.warning("답안을 입력한 후 채점 버튼을 눌러주세요.")

&#x20; else:

&#x20;   with st.spinner("AI 채점관이 문맥을 분석하여 채점 중입니다..."):

&#x20;     result = ai\_grade\_answer(

&#x20;         current\_card\["question"],

&#x20;         current\_card\["standard\_answers"],

&#x20;         current\_card\["total\_score"],

&#x20;         user\_input,

&#x20;         api\_key,

&#x20;     )



&#x20;     if "error" in result:

&#x20;       st.error(result\["error"])

&#x20;     else:

&#x20;       st.session\_state.last\_result = result

&#x20;       update\_anki\_schedule(

&#x20;           current\_card, result\["earned\_score"], result\["total\_score"]

&#x20;       )



\# 채점 결과 출력

if (

&#x20;   st.session\_state.last\_result

&#x20;   and "earned\_score" in st.session\_state.last\_result

):

&#x20; res = st.session\_state.last\_result

&#x20; st.markdown("---")

&#x20; st.subheader("📊 AI 채점 결과")

&#x20; st.markdown(

&#x20;     f"<p class='score-badge'>최종 점수: {res\['earned\_score']} /"

&#x20;     f" {res\['total\_score']} 점</p>",

&#x20;     unsafe\_allow\_html=True,

&#x20; )

&#x20; st.info(f"\*\*채점 총평:\*\* {res.get('detailed\_feedback', '')}")



&#x20; st.write("##### 🔍 세부 항목별 채점 상세:")

&#x20; for item in res.get("item\_results", \[]):

&#x20;   icon = "✅" if item\["is\_correct"] else "❌"

&#x20;   with st.expander(f"{icon} {item\['standard\_item']}"):

&#x20;     st.write(f"- \*\*내가 적은 내용:\*\* {item.get('user\_matched\_text') or '누락됨'}")

&#x20;     st.write(f"- \*\*채점 의견:\*\* {item.get('comment')}")



&#x20; if st.button("다음 문제로 이동 ➡️"):

&#x20;   st.session\_state.last\_result = None

&#x20;   st.rerun()

