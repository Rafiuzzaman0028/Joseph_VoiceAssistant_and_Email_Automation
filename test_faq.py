import requests

# Make sure your FastAPI server is running in another terminal using:
# uvicorn main:app --reload

url = "http://127.0.0.1:8000/api/faq/ask"

questions = [
    "How much is the deposit and when do I pay the rest?",
    "Can we bring our own food to the Liverpool venue?",
    "What happens if it rains on the day of the booking?",
    "Can we change the numbers of our group if some people drop out last minute?",
    "What should we wear for bubble soccer?",
    "Do you have food at the Manchester location?",
    "What is the best package for a large group of 18 people?",
    "How long is a typical session?",
    "Can we bring alcohol?",
    "Do we need to sign a waiver?",
    "What happens if the weather is bad?",
    "Is there a deposit required?",
    "What is the cancellation policy?",
    "Can we reschedule if needed?",
    "Are there age restrictions?",
    "What is included in the price?",
    "Where are the venues located?",
    "Do you offer team building packages?",
    "Can we book for a kids party?",
    "What payment methods do you accept?",
    "Is there parking available?",
    "Are the pitches indoors or outdoors?",
    "What happens if we are late?",
    "Can we bring our own cake?",
    "Do you provide referees?",
    "What safety equipment is provided?",
    "Can we bring our own food and drinks?",
    "Can we use restroom for 2 days in a row?"
]

print("Testing Voice Assistant FAQ (RAG)...\n")

for q in questions:
    print(f"User Asked: {q}")
    
    try:
        response = requests.post(url, json={"question": q})
        if response.status_code == 200:
            print(f"Voice Assistant Answered:\n{response.json().get('answer')}\n")
        else:
            print(f"Error: Server returned status {response.status_code}\n")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure it is running via 'uvicorn main:app --reload'")
        break
