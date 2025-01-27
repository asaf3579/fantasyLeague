import json
import sys
import bcrypt
from club import club
from dbHandler import DBHandler
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

bold_colors = ["red", "black", "blue", "purple", "pink", "orange", "green", "brown", "crimson", "indigo", "teal", "magenta", "turquoise"]


club_logos = {
    'בושנסקיניו': 'ob7.jpeg',
    'JakirFC': 'JAKIR FC.jpeg',
    'YNWA NAAMAN': 'YNWA_NAAMAN.jpeg',
    'עבדים FC': 'ABADIM FC.jpeg',
    'AC MALKA': 'AC MALKA.jpeg',
    'Hapoel Sakal': 'HAPOEL SAKAL.jpeg',
    'לילו ועוד 10': 'INTROP FC.jpeg',
    'בזויים FC':'nir FC.jpeg',
}

club_to_team = {
    'עבדים FC': 'team8',
    'Hapoel Sakal': 'team6',
    'JakirFC': 'team3',
    'בושנסקיניו': 'team2',
    'YNWA NAAMAN': 'team1',
    'לילו ועוד 10': 'team7',
    'AC MALKA': 'team4',
    'בזויים FC': 'team5',
}

team_to_club = {
    'team8': 'עבדים FC',
    'team6': 'Hapoel Sakal',
    'team3': 'JakirFC',
    'team2': 'בושנסקיניו',
    'team1': 'YNWA NAAMAN',
    'team7': 'לילו ועוד 10',
    'team4': 'AC MALKA',
    'team5': 'בזויים FC',

}
with open("config.json", "r") as json_file:
    data = json.load(json_file)


database_host = data["host"]
database_username = data["username"]
database_password = data["password"]
db_handler = DBHandler(database="fantasy_db_18qr", user="asaf", password="UWRdPm1BESAzsDEF32CVXYyfAolX6Kua", host="dpg-csbboj5umphs73badghg-a.frankfurt-postgres.render.com",
                       port=5432)
db_handler.create_users_messages_table()

# db_handler = DBHandler(database="fantasyLeague", user="postgres", password='naaman3579', host="localhost",
#                        port=5432)

def generate_random_color():
    if bold_colors:
        color = random.choice(bold_colors)
        bold_colors.remove(color)  # Remove the chosen color from the list
        return color
    else:
        return "black"  # Return None if the list is empty
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

    new_fixture = []
    for round in fixture:
        current_round = []
        for match in round:
            home_team = match[1]
            away_team = match[0]
            current_round.append((home_team,away_team))
        new_fixture.append(current_round)

    for round in new_fixture:
        fixture.append(round)

    # tmp = fixture[6]
    # fixture[6] = fixture[5]
    # fixture[5] = tmp
    # for i in range(7,13):
    #     tmp = fixture[i]
    #     fixture[i] = fixture[13]
    #     fixture[13] = tmp


    return fixture






def get_score_in_round(index,teams_score_per_round,team):
    if index < len(teams_score_per_round):
        return teams_score_per_round[index].get(team)
    return 0

def update_query(club_names_to_club):
    update_query = """
        UPDATE clubs_info
        SET \"bestScore\" = %s, \"winCount\" = %s, \"loseCount\" = %s, \"drawCount\" = %s, \"lastThreeMatches\" = %s, \"GF\" = %s, \"GA\" = %s
        WHERE \"name\"= %s;  
    """
    for club_name, club_class in club_names_to_club.items():
        values = (club_class.best_score,club_class.win_count,club_class.lose_count,club_class.draw_count,club_class.last_three_matches,club_class.GF,club_class.GA,club_class.name)
        db_handler.execute_query(update_query,values)

def update_club_info_table(clubs_score_next_round):
    select_query = "SELECT * FROM clubs_info"
    club_info = db_handler.fetch_data(select_query)
    club_names_to_club = {}
    for team in club_info:
        club_names_to_club[team[0]] = club(team[0], team[1], team[2], team[3], team[4], team[5],team[6],team[7])
    #todo: implement a function which update the club info table according to the last update.
    fixture = generate_rounds(app.config['teams'])
    round_to_update_matches = fixture[clubs_score_next_round.get('round') - 1]
    for match in round_to_update_matches:
        team_number_home = club_to_team.get(match[0])
        team_number_away = club_to_team.get(match[1])
        if team_number_home != "NoBody" and team_number_away != "NoBody":
            socre_home_team = clubs_score_next_round.get(team_number_home)
            score_away_team = clubs_score_next_round.get(team_number_away)
            if clubs_score_next_round.get(team_number_home) > clubs_score_next_round.get(team_number_away):
                club_names_to_club.get(match[0]).IncreaseWin(socre_home_team,score_away_team)
                club_names_to_club.get(match[1]).IncreaseLose(score_away_team,socre_home_team)
                #todo update home_team with a win and update away_team with a lose
            elif clubs_score_next_round.get(team_number_home) < clubs_score_next_round.get(team_number_away):
                club_names_to_club.get(match[1]).IncreaseWin(score_away_team,socre_home_team)
                club_names_to_club.get(match[0]).IncreaseLose(socre_home_team,score_away_team)
                #todo update away_team with a win and update home_team with a lose
            else:
                club_names_to_club.get(match[0]).IncreaseDraw(socre_home_team,score_away_team)
                club_names_to_club.get(match[1]).IncreaseDraw(socre_home_team,score_away_team)
                #todo update draw
    update_query(club_names_to_club)


app = Flask(__name__)
# app.config['GLOBAL_VARIABLE'] = update_from_sport5()
app.config['teams'] = ["YNWA NAAMAN", "בושנסקיניו", "JakirFC", "AC MALKA", "בזויים FC", "Hapoel Sakal", "לילו ועוד 10",
                       "עבדים FC"]
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db_chat = SQLAlchemy(app)

with app.app_context():
    db_chat.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
#



class User(UserMixin, db_chat.Model):
    id = db_chat.Column(db_chat.Integer, primary_key=True)
    username = db_chat.Column(db_chat.String(50), unique=True, nullable=False)
    password = db_chat.Column(db_chat.String(100), nullable=False)
    color = db_chat.Column(db_chat.String(7))  # Add the color field to store user's chat name color

# def get_user_by_name(user_name):
#     # Fetch user data from your data source based on user_id
#     select_query = "SELECT id, username, password FROM users WHERE username = %s;"
#     values = (username,)
#     user_data = db_handler.fetch_data(select_query, values)
#
#     if user_data:
#         # Create a User instance with user data and return it
#         user = User(user_id=user_data[0][0], username=user_data[0][1], password=user_data[0][2])
#         return user
#     else:
#         return None

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
      # Replace with your own function
    return User.query.get(int(user_id))


#new register with postgress
# @app.route('/register', methods=['GET','POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#
#         if not username or not password:
#             flash('Username and password are required.', 'error')
#         else:
#             # Hash the password (you can use bcrypt as you did before)
#             hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
#
#             # Insert user data into the PostgreSQL users table
#             insert_query = "INSERT INTO users (username, password, color) VALUES (%s, %s, %s);"
#             # values = (username, hashed_password, generate_random_color())
#             values = (username, password, generate_random_color())
#             db_handler.execute_query(insert_query, values)
#
#             flash('Registration successful. You can now log in.', 'success')
#             return redirect(url_for('login'))
#
#     return render_template('register.html')

# worked registration below
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
        else:
            # hashed_password = generate_password_hash(password, method='sha256')
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            new_user = User(username=username, password=hashed_password)
            new_user.color = generate_random_color()
            db_chat.session.add(new_user)
            db_chat.session.commit()
            #for backup postgresql
            flash('Registration successful. You can now log in.', 'success')
            insert_query = "INSERT INTO users (username, password, color) VALUES (%s, %s, %s);"
            # values = (username, hashed_password, generate_random_color())
            values = (username, password, new_user.color)
            db_handler.execute_query(insert_query, values)
            return redirect(url_for('login'))

    return render_template('register.html')


#login route with postgressql

# @app.route('/login', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#
#         # Fetch user data from the PostgreSQL users table
#         select_query = "SELECT id, username, password FROM users WHERE username = %s;"
#         values = (username,)
#         user_data = db_handler.fetch_data(select_query, values)
#
#         # bcrypt.checkpw(password.encode('utf-8'), user.password):
#         if user_data and password == user_data[0][2]:
#             print(user_data)
#             # Log in the user
#             user =User(int(user_data[0][0]))
#             # user = User.query.get(user_id)
#             # print(user)
#             # if user is None:
#             #     user = User(id=user_id)
#
#             login_user(user)
#             session['user_id'] = user.id
#             session['username'] = username
#             return redirect(url_for('standing'))
#         else:
#             flash('Invalid username or password.', 'error')
#
#     return render_template('login.html')


# login route which worked below
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            # Check the password (you should use proper password hashing here)
            if bcrypt.checkpw(password.encode('utf-8'), user.password):
                login_user(user)
                return redirect(url_for('standing'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            select_query = "SELECT id, username, password, color FROM users WHERE username = %s;"
            values = (username,)
            user_data = db_handler.fetch_data(select_query, values)

            if user_data and username == user_data[0][1] and password == user_data[0][2]:
                # User exists in PostgreSQL but not in SQLAlchemy
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                new_user = User(username=username, password=hashed_password)
                new_user.color = user_data[0][3]
                db_chat.session.add(new_user)
                db_chat.session.commit()

                login_user(new_user)  # Log in the newly created user
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
    select_query = '''
            SELECT messages.text, messages.timestamp, messages.color, messages.user_name
            FROM messages
            ORDER BY messages.timestamp ASC
            LIMIT 50;
        '''
    messages_data = db_handler.fetch_data(select_query)
    print(messages_data)
    messages = Message.query.all()

    return render_template('chat.html', messages=messages_data)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    text = data.get('text')
    if text:
        message = Message(text=text, user=current_user)
        db_chat.session.add(message)
        db_chat.session.commit()
        # #for backup in postgresql
        insert_query = "INSERT INTO messages (text, user_id, user_name, color) VALUES (%s, %s, %s, %s);"
        values = (text, current_user.id, current_user.username,current_user.color)
        db_handler.execute_query(insert_query, values)
        return jsonify(success=True, timestamp=message.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        return jsonify(success=False, error='Message text is required')
# Sending a message
# @app.route('/send_message', methods=['POST'])
# @login_required
# def send_message():
#     data = request.get_json()
#     text = data.get('text')
#
#     if text:
#         # Insert the message into the PostgreSQL messages table
#         insert_query = "INSERT INTO messages (text, user_id) VALUES (%s, %s);"
#         values = (text, current_user.id)
#         db_handler.execute_query(insert_query, values)
#
#         return jsonify(success=True, timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
#     else:
#         return jsonify(success=False, error='Message text is required')

# Fetching chat messages
# Fetching chat messages
# @app.route('/chat')
# @login_required
# def chat():
#
#     # Retrieve chat messages from the PostgreSQL messages table
#     select_query = '''
#         SELECT messages.text, messages.timestamp, users.color, users.username
#         FROM messages
#         INNER JOIN users ON messages.user_id = users.id
#         ORDER BY messages.timestamp ASC
#         LIMIT 50;
#     '''
#     messages_data = db_handler.fetch_data(select_query)
#     # messages = Message.query.all()
#     # print(messages)
#     print("============")
#     print(messages_data)
#     return render_template('chat.html', messages=messages_data)

@app.route('/standing')
def standing():

    team_data = []
    select_query = "SELECT * FROM clubs_info"
    results = db_handler.fetch_data(select_query)
    all_clubs = []
    for team in results:
        Myclub = club(team[0],team[1],team[2],team[3],team[4],team[5],team[6],team[7])
        all_clubs.append(Myclub)
    for i in range(len(all_clubs)):
        team_data.append(
            {'club': all_clubs[i].name, 'MP': all_clubs[i].GetMP(), 'W': all_clubs[i].win_count, 'D': all_clubs[i].draw_count, 'L': all_clubs[i].lose_count,'GF': all_clubs[i].GF,'GA': all_clubs[i].GA,'GD': all_clubs[i].GetGD(), 'score': all_clubs[i].getScore(), 'last_3': all_clubs[i].last_three_matches})
    # for i,team in enumerate(teams, start=1):
    #     team_data.append({'rank': i,'club': team,'MP': 0,'W': 0,'D': 0,'L': 0,'score': 0,'last_3': ['W', 'D', 'np']})
    # team_data.pop()
    sorted_data = sorted(team_data, key=lambda x: (-x['score'], -x['GD']))

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

    match_data = []
    # rounds = generate_rounds(['בושנסקיניו', "JakirFC", "YNWA NAAMAN", "עבדים FC", "AC Malka",
    #                              "Hapoel Sakal", "אינטרופ", "NoBody"])
    rounds = generate_rounds([team_to_club.get('team1'),team_to_club.get('team2'),team_to_club.get('team3'),team_to_club.get('team4'),team_to_club.get('team5'),team_to_club.get('team6'),team_to_club.get('team7'), team_to_club.get('team8')])

    for round ,matches in enumerate(rounds):
        list_match_of_current_round = []
        for match in matches:
            list_match_of_current_round.append({'home_team': match[0], 'away_team': match[1], 'home_score': get_score_in_round(round,teams_score_per_round,match[0]), 'away_score': get_score_in_round(round,teams_score_per_round,match[1])})
        match_data.append(list_match_of_current_round)
    # for matches in rounds:
    #     list_match_of_current_round = []
    #     for match in matches:
    #         list_match_of_current_round.append({'home_team': match[1], 'away_team': match[0], 'home_score': 0, 'away_score': 0})
    #     match_data.append(list_match_of_current_round)

    return render_template('all_matches.html', match_data=match_data)

@app.route('/top-scorers')
def top_scorers():
    # top_scorers_data = app.config['GLOBAL_VARIABLE']
    query = """
                     SELECT max(team1), max(team2), max(team3), max(team4), max(team5), max(team6), max(team7), max(team8)
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

    return render_template('top_scorers.html', top_scorers=sorted_data)

@app.route('/update-data', methods=['GET','POST'])
def update_data():

    return render_template('update_data.html')

@app.route('/update-data-process', methods=['GET','POST'])
def process_form():

    query = """
                 SELECT sum(team1), sum(team2), sum(team3), sum(team4), sum(team5), sum(team6), sum(team7), sum(team8)
                 FROM public.rounds_score;
                 """

    data_from_rounds_scoreDB = db_handler.fetch_data(query)
    data_from_sport5 = request.form
    # double_fixture = False
    query2 = 'SELECT max("roundNumber") FROM public.rounds_score;'
    last_round = int(db_handler.fetch_data(query2)[0][0])
    next_round = last_round + 1
    # if next_round == 7:
    #     double_fixture = True
    clubs_score_next_round = {'round': next_round}
    for team_number, (team, score) in enumerate(data_from_sport5.items()):
        score_of_team_next_round = int(score) - int(data_from_rounds_scoreDB[0][team_number])
        clubs_score_next_round[team] = score_of_team_next_round

    # todo
    insert_query = "INSERT INTO public.rounds_score (\"roundNumber\", team1, team2, team3, team4, team5, team6, team7, team8) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s);"
    values = (
    clubs_score_next_round.get('round'), clubs_score_next_round.get('team1'), clubs_score_next_round.get('team2'),
    clubs_score_next_round.get('team3'), clubs_score_next_round.get('team4'), clubs_score_next_round.get('team5'),
    clubs_score_next_round.get('team6'), clubs_score_next_round.get('team7'),clubs_score_next_round.get('team8'))
    db_handler.execute_query(insert_query, values)
    update_club_info_table(clubs_score_next_round)

    # if double_fixture:
    #     clubs_score_next_round['round'] = 8
    #     insert_query = "INSERT INTO public.rounds_score (\"roundNumber\", team1, team2, team3, team4, team5, team6, team7) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
    #     values = (
    #         clubs_score_next_round.get('round'), clubs_score_next_round.get('team1'),
    #         clubs_score_next_round.get('team2'),
    #         clubs_score_next_round.get('team3'), clubs_score_next_round.get('team4'),
    #         clubs_score_next_round.get('team5'),
    #         clubs_score_next_round.get('team6'), clubs_score_next_round.get('team7'))
    #     db_handler.execute_query(insert_query, values)
    #     update_club_info_table(clubs_score_next_round)


    # Retrieve scores from the form
    # team1_score = request.form.get('team1')
    # team2_score = request.form.get('team2')
    # team3_score = request.form.get('team3')
    # team4_score = request.form.get('team4')
    # team5_score = request.form.get('team5')
    # team6_score = request.form.get('team6')
    # team7_score = request.form.get('team7')
    # team8_score = request.form.get('team8')

    return redirect('/standing')


if __name__ == '__main__':
#     # username = sys.argv[1]
#     # password = sys.argv[2]
#     # host = sys.argv[3]
#     # db_handler = DBHandler(database="init_fanatasy", user=username, password=password, host=host,
#     #                        port=5432)
    with app.app_context():
        db_chat.create_all()

    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8000)
