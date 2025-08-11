import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GROQ_API_KEY = "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"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama3-70b-8192"

# Prompts
GET_SECRET_WORD_PROMPT = """
You are a game master. Generate a truly random common English word. 
Do not repeat previous words.
if user gets 5 yes consecutively give him a hint
Avoid examples. Just output **one** single common word. Nothing else.
"""
ANSWER_USER_PROMPT = """
You are playing a guessing game. Your secret word is: "{secret_word}".

The user asked: "{user_question}"

Reply with ONLY one of these words: "Yes", "No", or "Maybe". 
No explanation. No parentheses. No other words.
"""

ASK_QUESTION_PROMPT = """
You are trying to guess the user's secret word.

Use the following Q&A history to ask a strategic yes/no/maybe question to find out more:

{history}
"""

MAKE_GUESS_PROMPT = """
You are trying to guess the user's word based on this history:

{history}

Make a guess. Reply with just one word.
"""

def call_groq(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()

def build_history():
    return "\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.qa_history])

def reset_game():
    st.session_state.qa_history = []
    st.session_state.ai_secret_word = ""
    st.session_state.ai_question = ""
    st.session_state.user_word = ""
    st.session_state.guess_count = 0

# Initialize session state
if "mode" not in st.session_state:
    st.session_state.mode = "AI Guesses Your Word"
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []
if "ai_secret_word" not in st.session_state:
    st.session_state.ai_secret_word = ""
if "ai_question" not in st.session_state:
    st.session_state.ai_question = ""
if "user_word" not in st.session_state:
    st.session_state.user_word = ""
if "guess_count" not in st.session_state:
    st.session_state.guess_count = 0

# UI
st.set_page_config(page_title="🧠 Guess the Word - Groq", layout="centered")
st.title("🧠 Groq-Powered 'Guess the Word' Game")

mode = st.selectbox("🎮 Choose Game Mode:", ["You Guess AI's Word", "AI Guesses Your Word"])
st.session_state.mode = mode
st.divider()

# --- MODE 1: You Guess AI's Word ---
if mode == "You Guess AI's Word":
    if not st.session_state.ai_secret_word:
        st.session_state.ai_secret_word = call_groq(GET_SECRET_WORD_PROMPT)
        st.info("🤖 The AI has picked a secret word. You have 20 questions to find it!")

    user_question = st.text_input("❓ Ask a yes/no/maybe question:")
    if user_question and st.session_state.guess_count < 20:
        prompt = ANSWER_USER_PROMPT.format(
            secret_word=st.session_state.ai_secret_word,
            user_question=user_question
        )
        ai_response = call_groq(prompt)
        ai_response_clean = ai_response.lower().strip().split()[0]
        if ai_response_clean in ["yes", "no", "maybe"]:
            ai_response = ai_response_clean.capitalize()
        else:
            ai_response = "Maybe"
        st.session_state.qa_history.append((user_question, ai_response))
        st.session_state.guess_count += 1
        st.success(f"🤖 AI: {ai_response}")
        if ai_response_clean in ["maybe", "no"]:
                st.write("❌ Oops! Try Again")
    user_guess = st.text_input("🎯 Your final guess:")
    if user_guess:
        if user_guess.lower().strip() == st.session_state.ai_secret_word.lower().strip():
            st.balloons()
            st.success("🎉 Correct! You guessed the AI's word.")
        else:
            st.error("❌ Incorrect guess.")

    if st.session_state.guess_count >= 20:
        st.warning("😓 You've used all 20 guesses!")
        st.error(f"The AI's secret word was: **{st.session_state.ai_secret_word}**")

# --- MODE 2: AI Guesses Your Word ---
elif mode == "AI Guesses Your Word":
    if st.session_state.user_word == "":
        st.session_state.user_word = st.text_input("🧠 Enter your secret word (AI can't see it):", type="password")

    if st.session_state.user_word:
        if st.button("🤖 Ask Next Question") and st.session_state.guess_count < 20:
            history = build_history()
            prompt = ASK_QUESTION_PROMPT.format(history=history)
            ai_q = call_groq(prompt)
            st.session_state.ai_question = ai_q
            st.markdown(f"**🤖 AI Asks:** _{ai_q}_")

        if st.session_state.ai_question:
            col1, col2, col3 = st.columns(3)
            if col1.button("✅ Yes"):
                st.session_state.qa_history.append((st.session_state.ai_question, "Yes"))
                st.session_state.ai_question = ""
                st.session_state.guess_count += 1
            if col2.button("❌ No"):
                st.session_state.qa_history.append((st.session_state.ai_question, "No"))
                st.session_state.ai_question = ""
                st.session_state.guess_count += 1
            if col3.button("🤔 Maybe"):
                st.session_state.qa_history.append((st.session_state.ai_question, "Maybe"))
                st.session_state.ai_question = ""
                st.session_state.guess_count += 1

        if st.button("🎯 Let AI Guess"):
            history = build_history()
            prompt = MAKE_GUESS_PROMPT.format(history=history)
            guess = call_groq(prompt)
            st.markdown(f"**🤖 AI Guesses:** _{guess}_")
            correct = st.radio("Is the AI correct?", ["Not Yet", "Yes, that's correct!"])
            if correct == "Yes, that's correct!":
                st.balloons()
                st.success("🎉 The AI guessed your word!")
                st.session_state.ai_question = ""

        if st.session_state.guess_count >= 20:
            st.warning("😓 AI couldn't guess in 20 tries.")
            st.info(f"Your word was: **{st.session_state.user_word}**")

# --- Shared Q&A ---
with st.expander("📜 Question & Answer History"):
    for q, a in st.session_state.qa_history:
        st.write(f"**Q:** {q}\n**A:** {a}")

if st.button("🔁 Reset Game"):
    reset_game()
