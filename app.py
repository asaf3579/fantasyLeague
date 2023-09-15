from club import club
from dbHandler import DBHandler
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



club_logos = {
    'בושנסקיניו': 'macabi.jpeg',
    'JakirFC': 'Barcelona.jpeg',
    'YNWA NAAMAN': 'liverpool.jpeg',
    'עבדים FC': 'united.jpeg',
    'AC MALKA': 'milan.jpeg',
    'Hapoel Sakal': 'hapoel.jpeg',
    'INTROP FC': 'chealse.jpeg',
}

club_to_team = {
    'עבדים FC': 'team1',
    'Hapoel Sakal': 'team2',
    'JakirFC': 'team3',
    'בושנסקיניו': 'team4',
    'YNWA NAAMAN': 'team5',
    'INTROP FC': 'team6',
    'AC MALKA': 'team7',
    'NoBody': 'NoBody',
}

team_to_club = {
    'team1': 'עבדים FC',
    'team2': 'Hapoel Sakal',
    'team3': 'JakirFC',
    'team4': 'בושנסקיניו',
    'team5': 'YNWA NAAMAN',
    'team6': 'INTROP FC',
    'team7': 'AC MALKA',
    'NoBody': 'NoBody',

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

# def update_from_sport5():
#     chrome_options = Options()
#     chrome_options.add_argument('--headless')
#     driver_path = "chromedriver"
#     url = "https://fantasyleague.sport5.co.il/#!/Rank/League/1?Id=319828"  # Replace with the actual URL
#
#     driver = webdriver.Chrome(options=chrome_options)
#
#     # URL of the webpage you want to scrape
#
#     try:
#         # Send a GET request to the URL
#         driver.get(url)
#         wait = WebDriverWait(driver, 5)
#         teams_to_point_so_far = {'בושנסקיניו': 0, "JakirFC": 0, "YNWA NAAMAN": 0, "עבדים FC": 0, "AC Malka": 0,
#                                  "Hapoel Sakal": 0, "אינטרופ": 0}
#         for i in range(2, 9):
#             team_name = wait.until(EC.presence_of_element_located((By.XPATH,
#                                                                    f'/html/body/div[3]/div[3]/section/div/div/div/user-rank-table/table/tbody/tr[{i}]/td[2]'))).text
#             team_score = int(wait.until(EC.presence_of_element_located((By.XPATH,
#                                                                         f'/html/body/div[3]/div[3]/section/div/div/div/user-rank-table/table/tbody/tr[{i}]/td[4]'))).text)
#             teams_to_point_so_far[team_name] = team_score
#
#         sorted_teams = dict(sorted(teams_to_point_so_far.items(), key=lambda item: item[1], reverse=True))
#         team_data = []
#         for index, (team, score) in enumerate(sorted_teams.items(), start=1):
#             team_data.append({'rank': index,
#                               'name': team,
#                               'best_score': score,})
#     except requests.exceptions.RequestException as e:
#         return f"Error: {e}"
#
#     return team_data




def get_score_in_round(index,teams_score_per_round,team):
    if index < len(teams_score_per_round):
        return teams_score_per_round[index].get(team)
    return 0

def update_query(club_names_to_club):
    update_query = """
        UPDATE clubs_info
        SET \"bestScore\" = %s, \"winCount\" = %s, \"loseCount\" = %s, \"drawCount\" = %s, \"lastThreeMatches\" = %s
        WHERE \"name\"= %s;  
    """
    for club_name, club_class in club_names_to_club.items():
        values = (club_class.best_score,club_class.win_count,club_class.lose_count,club_class.draw_count,club_class.last_three_matches,club_class.name)
        db_handler.execute_query(update_query,values)

def update_club_info_table(clubs_score_next_round):
    select_query = "SELECT * FROM clubs_info"
    club_info = db_handler.fetch_data(select_query)
    club_names_to_club = {}
    for team in club_info:
        club_names_to_club[team[0]] = club(team[0], team[1], team[2], team[3], team[4], team[5])
    #todo: implement a function which update the club info table according to the last update.
    fixture = generate_rounds(app.config['teams'])
    round_to_update_matches = fixture[clubs_score_next_round.get('round') - 1]
    for match in round_to_update_matches:
        team_number_home = club_to_team.get(match[0])
        team_number_away = club_to_team.get(match[1])
        if team_number_home != "NoBody" and team_number_away != "NoBody":
            if clubs_score_next_round.get(team_number_home) > clubs_score_next_round.get(team_number_away):
                club_names_to_club.get(match[0]).IncreaseWin()
                club_names_to_club.get(match[1]).IncreaseLose()
                #todo update home_team with a win and update away_team with a lose
            elif clubs_score_next_round.get(team_number_home) < clubs_score_next_round.get(team_number_away):
                club_names_to_club.get(match[1]).IncreaseWin()
                club_names_to_club.get(match[0]).IncreaseLose()
                #todo update away_team with a win and update home_team with a lose
            else:
                club_names_to_club.get(match[0]).IncreaseDraw()
                club_names_to_club.get(match[1]).IncreaseDraw()
                #todo update draw
    update_query(club_names_to_club)



app = Flask(__name__)
# app.config['GLOBAL_VARIABLE'] = update_from_sport5()
app.config['teams'] = ['עבדים FC', "Hapoel Sakal", "JakirFC", "בושנסקיניו", "YNWA NAAMAN", "INTROP FC", "AC MALKA",
                       "NoBody"]
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db_chat = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db_handler = DBHandler(database="fantasyLeague", user="postgres", password='naaman3579', host="localhost",
                       port=5432)
class User(UserMixin, db_chat.Model):
    id = db_chat.Column(db_chat.Integer, primary_key=True)
    username = db_chat.Column(db_chat.String(50), unique=True, nullable=False)
    password = db_chat.Column(db_chat.String(100), nullable=False)

# Create a Message model with a foreign key to User
class Message(db_chat.Model):
    id = db_chat.Column(db_chat.Integer, primary_key=True)
    text = db_chat.Column(db_chat.String(200))
    timestamp = db_chat.Column(db_chat.DateTime, default=datetime.utcnow)
    user_id = db_chat.Column(db_chat.Integer, db_chat.ForeignKey('user.id'))
    user = db_chat.relationship('User', backref='messages')
# Create a User model


@app.route('/')
def index():
    return render_template('index.html')
@login_manager.user_loader
def load_user(user_id):
    # This function should return the User object for the given user_id
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
        else:
            hashed_password = generate_password_hash(password, method='sha256')
            new_user = User(username=username, password=hashed_password)
            db_chat.session.add(new_user)
            db_chat.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()


        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('standing'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Main chat page
@app.route('/chat')
@login_required
def chat():
    messages = Message.query.all()
    return render_template('chat.html', messages=messages)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    text = data.get('text')
    if text:
        message = Message(text=text, user=current_user)
        db_chat.session.add(message)
        db_chat.session.commit()
        return jsonify(success=True, timestamp=message.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        return jsonify(success=False, error='Message text is required')

@app.route('/standing')
def standing():

    team_data = []
    select_query = "SELECT * FROM clubs_info"
    results = db_handler.fetch_data(select_query)
    all_clubs = []
    for team in results:
        Myclub = club(team[0],team[1],team[2],team[3],team[4],team[5])
        all_clubs.append(Myclub)
    for i in range(len(all_clubs)):
        team_data.append(
            {'club': all_clubs[i].name, 'MP': all_clubs[i].GetMP(), 'W': all_clubs[i].win_count, 'D': all_clubs[i].draw_count, 'L': all_clubs[i].lose_count, 'score': all_clubs[i].getScore(), 'last_3': all_clubs[i].last_three_matches})
    # for i,team in enumerate(teams, start=1):
    #     team_data.append({'rank': i,'club': team,'MP': 0,'W': 0,'D': 0,'L': 0,'score': 0,'last_3': ['W', 'D', 'np']})
    # team_data.pop()
    sorted_data = sorted(team_data, key=lambda x: x['score'], reverse=True)

    return render_template('standing.html', teams=sorted_data,club_logos=club_logos)

@app.route('/all-matches')
def all_matches():
    select_query = "SELECT * FROM rounds_score"
    results = db_handler.fetch_data(select_query)[1:]
    teams_score_per_round = []
    for round in results:
        current_round_results = {}
        for i in range(1,len(round)):
            team = 'team'+str(i)
            current_round_results[team_to_club.get(team)] = round[i]
        teams_score_per_round.append(current_round_results)
    print(teams_score_per_round)


    print(results)
    match_data = []
    # rounds = generate_rounds(['בושנסקיניו', "JakirFC", "YNWA NAAMAN", "עבדים FC", "AC Malka",
    #                              "Hapoel Sakal", "אינטרופ", "NoBody"])
    rounds = generate_rounds([team_to_club.get('team1'),team_to_club.get('team2'),team_to_club.get('team3'),team_to_club.get('team4'),team_to_club.get('team5'),team_to_club.get('team6'),team_to_club.get('team7') , "NoBody"])

    for round ,matches in enumerate(rounds):
        list_match_of_current_round = []
        for match in matches:
            list_match_of_current_round.append({'home_team': match[0], 'away_team': match[1], 'home_score': get_score_in_round(round,teams_score_per_round,match[0]), 'away_score': get_score_in_round(round,teams_score_per_round,match[1])})
        match_data.append(list_match_of_current_round)
    for matches in rounds:
        list_match_of_current_round = []
        for match in matches:
            list_match_of_current_round.append({'home_team': match[1], 'away_team': match[0], 'home_score': 0, 'away_score': 0})
        match_data.append(list_match_of_current_round)

    return render_template('all_matches.html', match_data=match_data)

@app.route('/top-scorers')
def top_scorers():
    # top_scorers_data = app.config['GLOBAL_VARIABLE']
    query = """
                     SELECT max(team1), max(team2), max(team3), max(team4), max(team5), max(team6), max(team7)
                     FROM public.rounds_score;
                     """

    top_scorers_data = db_handler.fetch_data(query)[0]
    score_table = []
    for i,score in enumerate(top_scorers_data,start=1):
        scorer = {}
        team = 'team'+str(i)
        scorer['name'] = team_to_club.get(team)
        scorer['best_score'] = score
        score_table.append(scorer)
    sorted_data = sorted(score_table, key=lambda x: x['best_score'], reverse=True)
    for i, dict in enumerate(sorted_data,start=1):
        dict['rank'] = i
    print(sorted_data)

    return render_template('top_scorers.html', top_scorers=sorted_data)

@app.route('/update-data', methods=['GET','POST'])
def update_data():

    return render_template('update_data.html')

@app.route('/update-data-process', methods=['GET','POST'])
def process_form():
    query = """
                 SELECT sum(team1), sum(team2), sum(team3), sum(team4), sum(team5), sum(team6), sum(team7)
                 FROM public.rounds_score;
                 """

    data_from_rounds_scoreDB = db_handler.fetch_data(query)
    print("1",data_from_rounds_scoreDB)
    data_from_sport5 = request.form
    print("2",data_from_sport5)

    query2 = 'SELECT max("roundNumber") FROM public.rounds_score;'
    last_round = int(db_handler.fetch_data(query2)[0][0])
    print("3",last_round)
    next_round = last_round + 1
    clubs_score_next_round = {'round': next_round}
    for team_number, (team, score) in enumerate(data_from_sport5.items()):
        score_of_team_next_round = int(score) - int(data_from_rounds_scoreDB[0][team_number])
        clubs_score_next_round[team] = score_of_team_next_round

    # todo
    insert_query = "INSERT INTO public.rounds_score (\"roundNumber\", team1, team2, team3, team4, team5, team6, team7) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
    values = (
    clubs_score_next_round.get('round'), clubs_score_next_round.get('team1'), clubs_score_next_round.get('team2'),
    clubs_score_next_round.get('team3'), clubs_score_next_round.get('team4'), clubs_score_next_round.get('team5'),
    clubs_score_next_round.get('team6'), clubs_score_next_round.get('team7'))
    db_handler.execute_query(insert_query, values)
    print(clubs_score_next_round)
    update_club_info_table(clubs_score_next_round)

    print(clubs_score_next_round)
    print("Updating data...")

    # Retrieve scores from the form
    team1_score = request.form.get('team1')
    team2_score = request.form.get('team2')
    team3_score = request.form.get('team3')
    team4_score = request.form.get('team4')
    team5_score = request.form.get('team5')
    team6_score = request.form.get('team6')
    team7_score = request.form.get('team7')
    # team8_score = request.form.get('team8')

    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
        db_chat.create_all()
    app.run(debug=True)