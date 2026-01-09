import requests
import sys

# Usage: python test_prod_login.py <username> <password>

BASE_URL = "https://edusmart.ign3el.com"
LOGIN_URL = f"{BASE_URL}/api/auth/token"

if len(sys.argv) < 3:
    print("Usage: python test_prod_login.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

print(f"Testing Login against: {LOGIN_URL}")
print(f"User: {username}")

try:
    response = requests.post(
        LOGIN_URL,
        data={
            "username": username,
            "password": password,
            "grant_type": "password"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200:
        print("\n✅ SUCCESS! Credentials are valid on Production.")
    elif response.status_code == 401:
        print("\n❌ FAILED: 401 Unauthorized.")
        print("This means the Production Database does NOT have this user/password combination.")
        print("Suggestion: create a NEW account on the production server.")
    else:
        print(f"\n⚠️ Unexpected Error: {response.status_code}")

except Exception as e:
    print(f"Network Error: {e}")
