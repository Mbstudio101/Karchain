from bs4 import BeautifulSoup
import re

with open("fanduel_nba.html", "r") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find elements that might be odds
# Odds usually look like -110, +150, -5.5, 210.5
odds_pattern = re.compile(r'^[-+]?\d+(\.\d+)?$')

print("Searching for odds-like text nodes...")
count = 0
for element in soup.find_all(string=True):
    text = element.strip()
    if text and (text.startswith("-") or text.startswith("+")) and len(text) < 8:
        # Check if it looks like a number
        # typical odds: -110, +200, -4.5
        if re.match(r'^[-+]?\d+(\.\d+)?$', text) or "O " in text or "U " in text:
             parent = element.parent
             # Go up to the button/clickable div
             clickable = parent
             for _ in range(3):
                 if clickable and (clickable.name == 'button' or clickable.get('role') == 'button' or clickable.get('aria-label')):
                     break
                 clickable = clickable.parent
             
             if clickable:
                 print(f"Found '{text}' in clickable <{clickable.name}> with aria-label='{clickable.get('aria-label')}' class='{clickable.get('class')}'")
             else:
                 print(f"Found '{text}' but no clickable parent found. Parent: <{parent.name} class='{parent.get('class')}'>")
             
             count += 1
             if count > 30: 
                 break

print("\nSearching for team names to locate game containers...")
teams = ["New York Knicks"]
for team in teams:
    elements = soup.find_all(string=re.compile(team, re.IGNORECASE))
    for el in elements:
        parent = el.parent
        if parent.name == 'span':
            print(f"Found '{team}' in <{parent.name}>. Traversing up...")
            # Go up let's say 6 levels to find the row/card
            curr = parent
            for i in range(10):
                curr = curr.parent
                if curr:
                    print(f"Level {i+1}: <{curr.name} class='{curr.get('class')}' aria-label='{curr.get('aria-label')}'>")
                    # If this looks like a game container (has multiple team names or odds), print deeper info
                    text_content = curr.get_text(" | ", strip=True)
                    if "Celtics" in text_content and ("+1" in text_content or "-1" in text_content):
                        print(f"--- POTENTIAL GAME CARD FOUND at Level {i+1} ---")
                        print(f"Text content: {text_content}")
                        # Print generic structure of children
                        print("Children tags:")
                        for child in curr.find_all(recursive=False):
                             print(f"  <{child.name} class='{child.get('class')}' aria-label='{child.get('aria-label')}'>")
                        break
            break
