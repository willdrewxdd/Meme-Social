import streamlit as st
import requests
import base64
import urllib.parse

# Configuration
API_BASE_URL = "https://meme-social.onrender.com"

st.set_page_config(page_title="Meme Social", layout="wide")

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

# Authorization header helper
def get_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

# Login and Registration Page
def login_page():
    st.title("🚀 Welcome to Meme Social")

    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    if email and password:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Login", type="primary", use_container_width=True):
                login_data = {"username": email, "password": password}
                response = requests.post(f"{API_BASE_URL}/auth/jwt/login", data=login_data)

                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]
                    
                    # Fetch user details
                    user_response = requests.get(f"{API_BASE_URL}/users/me", headers=get_headers())
                    if user_response.status_code == 200:
                        st.session_state.user = user_response.json()
                        st.rerun()
                    else:
                        st.error("Failed to fetch user data.")
                else:
                    st.error("Invalid email or password!")

        with col2:
            if st.button("Sign Up", type="secondary", use_container_width=True):
                signup_data = {"email": email, "password": password}
                response = requests.post(f"{API_BASE_URL}/auth/register", json=signup_data)

                if response.status_code == 201:
                    st.success("Account created! You can now login.")
                else:
                    error_detail = response.json().get("detail", "Registration failed")
                    st.error(f"Error: {error_detail}")
    else:
        st.info("Please enter your email and password to continue.")

# Upload Page
def upload_page():
    st.title("📸 Share Something")

    uploaded_file = st.file_uploader("Choose media", type=['png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'webm'])
    caption = st.text_area("Caption:", placeholder="What's on your mind?")

    if uploaded_file and st.button("Share", type="primary"):
        with st.spinner("Uploading to cloud..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"caption": caption}
            response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data, headers=get_headers())

            if response.status_code == 200:
                st.success("Successfully posted!")
                st.rerun()
            else:
                st.error(f"Upload failed! (Status: {response.status_code})")

# ImageKit text overlay helper
def encode_text_for_overlay(text):
    if not text:
        return ""
    base64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return urllib.parse.quote(base64_text)

# ImageKit URL transformation helper
def create_transformed_url(original_url, transformation_params, caption=None):
    if caption:
        encoded_caption = encode_text_for_overlay(caption)
        text_overlay = f"l-text,ie-{encoded_caption},ly-N10,lx-10,fs-10,co-white,bg-000000A0,l-end"
        transformation_params = text_overlay

    if not transformation_params:
        return original_url

    parts = original_url.split("/")
    base_url = "/".join(parts[:4])
    file_path = "/".join(parts[4:])
    return f"{base_url}/tr:{transformation_params}/{file_path}"

# Main Feed Page
def feed_page():
    st.title("🏠 Feed")

    with st.spinner("Loading latest posts..."):
        try:
            response = requests.get(f"{API_BASE_URL}/feed", headers=get_headers())
            if response.status_code == 200:
                posts = response.json()["posts"]

                if not posts:
                    st.info("No posts yet. Be the first to share!")
                    return

                for post in posts:
                    st.markdown("---")
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{post['email']}** • {post['created_at'][:10]}")
                    with col2:
                        # Allow deletion only if owner
                        if post.get('is_owner', False):
                            if st.button("🗑️", key=f"del_{post['id']}", help="Delete post"):
                                res = requests.delete(f"{API_BASE_URL}/posts/{post['id']}", headers=get_headers())
                                if res.status_code == 200:
                                    st.rerun()
                                else:
                                    st.error("Delete failed.")

                    # Display media
                    if post['file_type'] == 'image':
                        st.image(post['url'], width=500)
                    else:
                        st.video(post['url'])
                    
                    st.caption(post.get('caption', ''))
            else:
                st.error("Failed to load feed.")
        except Exception as e:
            st.error(f"Connection error: {e}")

# Application Entry Point
if st.session_state.user is None:
    login_page()
else:
    # Sidebar navigation
    st.sidebar.title(f"👋 Hello!")
    st.sidebar.write(f"{st.session_state.user['email']}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.token = None
        st.rerun()

    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation:", ["🏠 Feed", "📸 Upload"])

    if page == "🏠 Feed":
        feed_page()
