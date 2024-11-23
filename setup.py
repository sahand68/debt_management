import os

port = int(os.environ.get("PORT", 8501))

def setup_config():
    config_dir = os.path.join(os.path.expanduser('~'), '.streamlit')
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, 'config.toml')
    with open(config_path, 'w') as f:
        f.write(f"""
[server]
port = {port}
enableCORS = false
enableXsrfProtection = false
address = "0.0.0.0"

[browser]
gatherUsageStats = false
        """)

if __name__ == "__main__":
    setup_config()