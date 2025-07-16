import streamlit as st
from google.generativeai import GenerativeModel, configure
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="英単語クイズ", page_icon="📒")
st.title("英単語クイズ")

# APIキー入力フォーム
if "api_key" not in st.session_state or st.session_state.api_key is None:
    st.info("あなたのGoogle Gemini APIキーを入力してください。")
    api_key_input = st.text_input("APIキーを入力", type="password", key="api_input")
    if st.button("APIキーを設定"):
        if api_key_input.strip():
            st.session_state.api_key = api_key_input.strip()
            st.success("APIキーが設定されました。もう一度クリックして続行してください。")
        else:
            st.error("正しいキーを入力してください。")
    st.stop()

# APIキー設定
configure(api_key=st.session_state.api_key)
model = GenerativeModel("models/gemini-2.5-pro")

# セッション初期化
defaults = {
    "questions": [],
    "current_q": 0,
    "score": 0,
    "user_answers": [],
    "difficulty": None,
    "mode": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# プロンプト生成など省略（元のまま）

# 難易度・出題形式の選択
if not st.session_state.questions:
    st.subheader("難易度と出題形式を選んでください")

    difficulty = st.radio("難易度", ["初級", "中級", "上級"], horizontal=True)
    mode_label = st.radio("出題形式", ["英語 → 日本語", "日本語 → 英語"], horizontal=True)
    mode = "en_to_ja" if mode_label == "英語 → 日本語" else "ja_to_en"

    if st.button("クイズをはじめる"):
        with st.spinner("問題を作成中..."):
            st.session_state.difficulty = difficulty
            st.session_state.mode = mode
            st.session_state.questions = generate_questions(difficulty=difficulty, mode=mode)
        # rerunしない→questionsがセットされたことで次の分岐へ進む

# 出題と回答
elif st.session_state.current_q < len(st.session_state.questions):
    qnum = st.session_state.current_q
    question = st.session_state.questions[qnum]
    mode = st.session_state.mode

    st.subheader(f"第 {qnum+1} 問")

    if mode == "en_to_ja":
        st.write(f"単語: **{question['word']}**")
        user_answer = st.text_input("意味（日本語）を入力してください", key=f"answer_{qnum}")
        correct = question["meaning"]
        prompt_label = question["word"]
    else:
        st.write(f"意味: **{question['meaning']}**")
        user_answer = st.text_input("英単語を入力してください", key=f"answer_{qnum}")
        correct = question["word"]
        prompt_label = question["meaning"]

    if st.button("回答する"):
        is_correct = user_answer.strip().lower() in correct.lower()
        st.session_state.user_answers.append({
            "出題": prompt_label,
            "正解": correct,
            "あなたの回答": user_answer,
            "結果": "⭕ 正解" if is_correct else "❌ 不正解"
        })
        if is_correct:
            st.session_state.score += 1
        st.session_state.current_q += 1
        # rerunしない。次回描画時にcurrent_qが増えているので問題が切り替わる

# 結果表示/CSVダウンロード
else:
    st.success(f"クイズ終了！（難易度：{st.session_state.difficulty}｜出題形式：{'英→日' if st.session_state.mode=='en_to_ja' else '日→英'}）")
    st.markdown(f"## あなたのスコア: {st.session_state.score} / 5")

    df = pd.DataFrame(st.session_state.user_answers)
    df.index += 1
    st.table(df)

    csv = df.to_csv(index=False)
    now = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"quiz_result_{now}.csv"

    st.download_button(
        label="結果をCSVで保存",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )

# リスタート
if st.button("もう一度チャレンジする"):
    st.session_state.questions = []
    st.session_state.user_answers = []
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.difficulty = None
    st.session_state.mode = None
    # rerunしない→状態更新のみ。次回描画時に初期画面に戻る

    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.difficulty = None
    st.session_state.mode = None
    st.experimental_rerun()
