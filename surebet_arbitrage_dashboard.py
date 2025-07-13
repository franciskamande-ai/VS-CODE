import streamlit as st
from datetime import datetime, timedelta
import json
import os
import hashlib

# --- PAGE CONFIG ---
st.set_page_config(page_title="3-Way Surebet Analyzer", layout="centered")

# --- SESSION INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- FILE SETUP ---
USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USER_DB, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()

# --- SIDEBAR INFO ---
st.sidebar.markdown("## 📊 Subscription Status")
if st.session_state.logged_in:
    user = users.get(st.session_state.user_email)
    if user:
        signup_date = datetime.strptime(user["signup_date"], "%Y-%m-%d")
        today = datetime.today()
        trial_days_left = max(0, 3 - (today - signup_date).days)
        if user.get("is_subscribed"):
            st.sidebar.success(f"✅ Subscribed\nExpiry: {user.get('subscription_expiry', '∞')}")
        elif user.get("is_affiliate"):
            st.sidebar.info("🤝 Affiliate Access")
        else:
            st.sidebar.warning(f"🕐 Free Trial - {trial_days_left} day(s) left")

st.sidebar.markdown("---")
st.sidebar.markdown("## 📘 How This App Works")
st.sidebar.info("""
This app uses **implied probability** to calculate
surebet opportunities from bookmaker odds.

💡 If a surebet exists, it tells you exactly how much
to bet on each outcome to guarantee profit –
no matter the match result.
""")

st.sidebar.markdown("## ❤️ Support This Project")
st.sidebar.markdown("- Pochi La Biashara: `0769043920`")

st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ Made by **Francis Kamande**")

# --- Admin Panel (Only for fkamande264@gmail.com) ---
ADMIN_EMAIL = "fkamande264@gmail.com"
if st.session_state.logged_in and st.session_state.user_email == ADMIN_EMAIL:
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🛠 Admin Panel")

    with st.sidebar.expander("🔎 View All Users"):
        for u_email, u_data in users.items():
            sub = "✅ Subscribed" if u_data.get("is_subscribed") else "❌ Not Subscribed"
            st.markdown(f"**{u_email}**  \n{sub}  \n🗓 Signed up: {u_data['signup_date']}  \n---")

    st.sidebar.markdown("### ✅ Activate a User")
    email_to_activate = st.sidebar.text_input("User Email to Activate")
    if st.sidebar.button("Activate Now"):
        if email_to_activate in users:
            users[email_to_activate]["is_subscribed"] = True
            users[email_to_activate]["subscription_expiry"] = str(datetime.today() + timedelta(days=30))
            save_users(users)
            st.sidebar.success(f"{email_to_activate} is now activated.")
        else:
            st.sidebar.error("User not found.")

# --- LOGIN FLOW ---
if not st.session_state.logged_in:
    st.title("🔐 Login to Access 3-Way Surebet Analyzer")

    auth_mode = st.radio("Select mode:", ["Login", "Register"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submit = st.button("Submit")

    if submit and email and password:
        if auth_mode == "Register":
            if email in users:
                st.warning("User already exists. Please login.")
            else:
                users[email] = {
                    "password": hash_password(password),
                    "signup_date": str(datetime.today().date()),
                    "is_subscribed": False,
                    "subscription_expiry": None,
                    "is_affiliate": False
                }
                save_users(users)
                st.success("Account created. Please login.")

        elif auth_mode == "Login":
            user = users.get(email)
            if not user or user["password"] != hash_password(password):
                st.error("Invalid email or password.")
            else:
                if email == ADMIN_EMAIL:
                    user["is_subscribed"] = True
                    save_users(users)

                signup_date = datetime.strptime(user["signup_date"], "%Y-%m-%d")
                today = datetime.today()
                days_used = (today - signup_date).days
                is_affiliate = user.get("is_affiliate", False)

                # Check subscription expiry
                if user.get("is_subscribed") and user.get("subscription_expiry"):
                    expiry_date = datetime.strptime(user["subscription_expiry"], "%Y-%m-%d")
                    if expiry_date < today:
                        user["is_subscribed"] = False
                        user["subscription_expiry"] = None
                        save_users(users)

                if user.get("is_subscribed") or is_affiliate or days_used <= 3:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.warning("⏳ Trial expired. Please subscribe to unlock full access.")
                    st.markdown("""
💳 **Payment Instructions**

- Send **KES 100** to **Pochi la Biashara: `0769043920`**
- After payment, WhatsApp your **email** to [📲 `0769043920`](https://wa.me/254769043920)
- We’ll activate your account within minutes.

🕐 *Need help? Just tap the WhatsApp link above.*
""")

# --- LOGGED IN VIEW ---
if st.session_state.logged_in:
    st.title("⚽ Global Arbitrage Calculator (Surebet)")

    total_ksh = st.number_input("💰 Total Amount to Bet (KES)", min_value=1.0, value=100.0, step=1.0)

    team_a = st.text_input("🏟 Team A (Home)", "Team A")
    team_b = st.text_input("🏟 Team B (Away)", "Team B")

    col1, col2, col3 = st.columns(3)

    with col1:
        home_odds = st.number_input("🏠 Best Odds for Team A Win", min_value=1.01, value=3.90, step=0.01)

    with col2:
        draw_odds = st.number_input("🤝 Best Odds for Draw", min_value=1.01, value=3.60, step=0.01)

    with col3:
        away_odds = st.number_input("🛋 Best Odds for Team B Win", min_value=1.01, value=2.20, step=0.01)

    if st.button("🧮 CALCULATE SUREBET"):
        # --- CALCULATIONS ---
        p1 = 1 / home_odds
        px = 1 / draw_odds
        p2 = 1 / away_odds
        total_implied = p1 + px + p2

        st.write(f"📊 **Total Implied Probability**: {round(total_implied * 100, 2)}%")

        if total_implied >= 1:
            st.error("❌ No arbitrage opportunity – total implied probability is above 100%.")
        else:
            stake_home = (p1 / total_implied) * total_ksh
            stake_draw = (px / total_implied) * total_ksh
            stake_away = (p2 / total_implied) * total_ksh

            payout_home = stake_home * home_odds
            payout_draw = stake_draw * draw_odds
            payout_away = stake_away * away_odds

            guaranteed_payout = round(min(payout_home, payout_draw, payout_away), 2)
            guaranteed_profit = round(guaranteed_payout - total_ksh, 2)

            st.success(f"✅ Arbitrage Found! Guaranteed Profit: KES {guaranteed_profit} ({round((guaranteed_profit / total_ksh) * 100, 2)}%)")

            st.markdown("### 💡 Optimal Bet Distribution")
            st.table({
                "Outcome": [f"{team_a} Win", "Draw", f"{team_b} Win"],
                "Odds": [home_odds, draw_odds, away_odds],
                "Stake (KES)": [round(stake_home, 2), round(stake_draw, 2), round(stake_away, 2)],
                "Payout (KES)": [round(payout_home, 2), round(payout_draw, 2), round(payout_away, 2)]
            })

    st.markdown("---")
    st.markdown("### 🚨 Help & Support")
    whatsapp_number = "254769043920"
    wa_url = f"https://wa.me/{whatsapp_number}"
    st.markdown(f"[📲 Contact Support on WhatsApp](<{wa_url}>)")
