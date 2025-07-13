import streamlit as st
from datetime import datetime, timedelta
import hashlib
from supabase import create_client, Client

# --- SUPABASE CONFIG ---
SUPABASE_URL = "https://pzmzhosembarfvewtout.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB6bXpob3NlbWJhcmZ2ZXd0b3V0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0MjkxNTcsImV4cCI6MjA2ODAwNTE1N30.jU72hLw929y1qp2ZFJkFI5n52XuVYUfUSh-sHSOr6lU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- PAGE CONFIG ---
st.set_page_config(page_title="3-Way Surebet Analyzer", layout="centered")

# --- SESSION INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# --- UTILS ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(email):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def save_user(user_data):
    supabase.table("users").insert(user_data).execute()

def update_user(email, updates):
    supabase.table("users").update(updates).eq("email", email).execute()

# --- ADMIN EMAIL ---
ADMIN_EMAIL = "fkamande264@gmail.com"

# --- SIDEBAR INFO ---
st.sidebar.markdown("## 📊 Subscription Status")
if st.session_state.logged_in:
    user = get_user(st.session_state.user_email)
    if user:
        if user["email"] == ADMIN_EMAIL:
            st.sidebar.success("👑 Welcome, Admin. Subscription is unlimited.")
        else:
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
if st.session_state.logged_in and st.session_state.user_email == ADMIN_EMAIL:
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🛠 Admin Panel")

    with st.sidebar.expander("🔎 View All Users"):
        users = supabase.table("users").select("*").execute().data
        for u in users:
            sub = "✅ Subscribed" if u.get("is_subscribed") else "❌ Not Subscribed"
            st.markdown(f"**{u['email']}**  \n{sub}  \n🗓 Signed up: {u['signup_date']}  \n---")

    st.sidebar.markdown("### ✅ Activate a User")
    email_to_activate = st.sidebar.text_input("User Email to Activate")
    if st.sidebar.button("Activate Now"):
        update_user(email_to_activate, {
            "is_subscribed": True,
            "subscription_expiry": str(datetime.today() + timedelta(days=30))
        })
        st.sidebar.success(f"{email_to_activate} is now activated.")

# --- LOGIN / REGISTER VIEW ---
if not st.session_state.logged_in:
    st.title("🔐 Login to Access Surebet Calculator")
    mode = st.radio("Choose:", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Submit") and email and password:
        user = get_user(email)
        if mode == "Register":
            if user:
                st.warning("User already exists.")
            else:
                save_user({
                    "email": email,
                    "password": hash_password(password),
                    "signup_date": str(datetime.today().date()),
                    "is_subscribed": False,
                    "subscription_expiry": None,
                    "is_affiliate": False
                })
                st.success("Account created. Please login.")
        else:
            if not user or user["password"] != hash_password(password):
                st.error("Invalid credentials.")
            else:
                if email != ADMIN_EMAIL:
                    today = datetime.today()
                    expiry = user.get("subscription_expiry")
                    expired = expiry and datetime.strptime(expiry, "%Y-%m-%d") < today
                    if expired:
                        update_user(email, {"is_subscribed": False, "subscription_expiry": None})
                        user["is_subscribed"] = False

                    days_used = (today - datetime.strptime(user["signup_date"], "%Y-%m-%d")).days
                    if not user.get("is_subscribed") and not user.get("is_affiliate") and days_used > 3:
                        st.warning("Trial expired. Please subscribe to continue.")
                        st.stop()

                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()

# --- MAIN APP ---
if st.session_state.logged_in:
    st.title("⚽ Global Surebet Calculator")

    with st.form("surebet_form"):
        total_ksh = st.number_input("💰 Total Amount to Bet (KES)", min_value=1.0, value=100.0)
        team_a = st.text_input("🏠 Team A", "Team A")
        team_b = st.text_input("🛫 Team B", "Team B")

        col1, col2, col3 = st.columns(3)
        with col1:
            home_odds = st.number_input("Team A Win Odds", min_value=1.01, value=3.90)
        with col2:
            draw_odds = st.number_input("Draw Odds", min_value=1.01, value=3.60)
        with col3:
            away_odds = st.number_input("Team B Win Odds", min_value=1.01, value=2.20)

        submitted = st.form_submit_button("📈 Calculate Surebet")

    if submitted:
        p1 = 1 / home_odds
        px = 1 / draw_odds
        p2 = 1 / away_odds
        total_implied = p1 + px + p2

        st.write(f"📊 Total Implied Probability: {round(total_implied * 100, 2)}%")

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

            st.success(f"✅ Arbitrage Found! Profit: KES {guaranteed_profit} ({round((guaranteed_profit / total_ksh) * 100, 2)}%)")

            st.markdown("### 🔢 Optimal Stake Distribution")
            st.table({
                "Outcome": [f"{team_a} Win", "Draw", f"{team_b} Win"],
                "Odds": [home_odds, draw_odds, away_odds],
                "Stake (KES)": [round(stake_home, 2), round(stake_draw, 2), round(stake_away, 2)],
                "Payout (KES)": [round(payout_home, 2), round(payout_draw, 2), round(payout_away, 2)]
            })
