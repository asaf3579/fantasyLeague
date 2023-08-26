from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
club_logos = {
    'בושנסקיניו': 'macabi.jpeg',
    'JakirFC': 'Barcelona.jpeg',
    'YNWA NAAMAN': 'liverpool.jpeg',
    'עבדים FC': 'united.jpeg',
    'AC Malka': 'milan.jpeg',
    'Hapoel Sakal': 'hapoel.jpeg',
    'אינטרופ': 'chealse.jpeg',
    # Add more club names and logo URLs
}
def generate_rounds(teams):
    num_teams = len(teams)
    num_rounds = num_teams - 1

    fixture = []

    for _ in range(num_rounds):
        round_matches = []

        for i in range(num_teams // 2):
            match = (teams[i], teams[num_teams - 1 - i])
            round_matches.append(match)

        fixture.append(round_matches)

        # Rotate teams for the next round
        teams = [teams[0]] + [teams[-1]] + teams[1:num_teams - 1]
    # print(fixture)
    return fixture

def update_from_sport5():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver_path = "chromedriver"
    url = "https://fantasyleague.sport5.co.il/#!/Rank/League/1?Id=319828"  # Replace with the actual URL

    driver = webdriver.Chrome(options=chrome_options)

    # URL of the webpage you want to scrape

    try:
        # Send a GET request to the URL
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        teams_to_point_so_far = {'בושנסקיניו': 0, "JakirFC": 0, "YNWA NAAMAN": 0, "עבדים FC": 0, "AC Malka": 0,
                                 "Hapoel Sakal": 0, "אינטרופ": 0}
        for i in range(2, 9):
            team_name = wait.until(EC.presence_of_element_located((By.XPATH,
                                                                   f'/html/body/div[3]/div[3]/section/div/div/div/user-rank-table/table/tbody/tr[{i}]/td[2]'))).text
            team_score = int(wait.until(EC.presence_of_element_located((By.XPATH,
                                                                        f'/html/body/div[3]/div[3]/section/div/div/div/user-rank-table/table/tbody/tr[{i}]/td[4]'))).text)
            teams_to_point_so_far[team_name] = team_score

        sorted_teams = dict(sorted(teams_to_point_so_far.items(), key=lambda item: item[1], reverse=True))
        team_data = []
        for index, (team, score) in enumerate(sorted_teams.items(), start=1):
            team_data.append({'rank': index,
                              'name': team,
                              'best_score': score,})
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

    return team_data


app = Flask(__name__)
app.config['GLOBAL_VARIABLE'] = update_from_sport5()
app.config['teams'] = ['בושנסקיניו', "JakirFC", "YNWA NAAMAN", "עבדים FC", "AC Malka", "Hapoel Sakal", "אינטרופ",
                       "NoBody"]



@app.route('/')
def index():
    # team_data = app.config['GLOBAL_VARIABLE']
    teams = app.config['teams']
    team_data = []
    #todo implement a read from data base
    for i,team in enumerate(teams, start=1):
        team_data.append({'rank': i,'club': team,'MP': 0,'W': 0,'D': 0,'L': 0,'score': 0,'last_3': ['W', 'D', 'np']})
    team_data.pop()
    # sorted_data = sorted(team_data, key=lambda x: x['score'], reverse=True)

    return render_template('index.html', teams=team_data,club_logos=club_logos)



@app.route('/all-matches')
def all_matches():
    match_data = []
    rounds = generate_rounds(['בושנסקיניו', "JakirFC", "YNWA NAAMAN", "עבדים FC", "AC Malka",
                                 "Hapoel Sakal", "אינטרופ", "NoBody"])
    for mathces in rounds:
        list_match_of_current_round = []
        for match in mathces:
            list_match_of_current_round.append({'home_team': match[0], 'away_team': match[1], 'home_score': 0, 'away_score': 0})
        match_data.append(list_match_of_current_round)
    for mathces in rounds:
        list_match_of_current_round = []
        for match in mathces:
            list_match_of_current_round.append({'home_team': match[1], 'away_team': match[0], 'home_score': 0, 'away_score': 0})
        match_data.append(list_match_of_current_round)

    return render_template('all_matches.html', match_data=match_data)
# app.py

# ... (your existing code)

@app.route('/top-scorers')
def top_scorers():
    top_scorers_data = app.config['GLOBAL_VARIABLE']
    return render_template('top_scorers.html', top_scorers=top_scorers_data)

# ... (your existing code)


if __name__ == '__main__':

    app.run(debug=True)
