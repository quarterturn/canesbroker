import datetime
import time
import os
import requests
from lib import nhl
import atexit
import os
import time
import paho.mqtt.client as paho
import ssl

broker = "localhost"
port = 1883
user = "admin"
password = "ftgvcdrU2!"

#main_dir = os.getcwd()
main_dir = "/home/ubuntu/canesbroker"

# do something on exit
def clearOnExit():
    print("Exiting.")

atexit.register(clearOnExit)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # print("Connected OK, returned: ", rc)
        client.connected_flag = True
    else:
        print("Connect failed, returned: ", rc)

client1 = paho.Client("control1")
#client1.tls_set(main_dir + '/ca.crt', tls_version=ssl.PROTOCOL_TLSv1_2)
#client1.tls_insecure_set(True)
client1.on_connect = on_connect
client1.username_pw_set(user, password)
client1.loop_start()
client1.connect(broker, port)


def sleep(sleep_period):
    """ Function to sleep if not in season or no game.
    Inputs sleep period depending if it's off season or no game."""

    # Get current time
    now = datetime.datetime.now()
    # Set sleep time for no game today
    if "day" in sleep_period:
        delta = datetime.timedelta(hours=12)
    # Set sleep time for not in season
    elif "season" in sleep_period:
        # If in August, 31 days else 30
        if now.month is 8:
            delta = datetime.timedelta(days=31)
        else:
            delta = datetime.timedelta(days=30)
    next_day = datetime.datetime.today() + delta
    next_day = next_day.replace(hour=12, minute=10)
    sleep = next_day - now
    sleep = sleep.total_seconds()
    time.sleep(sleep)


def setup_nhl():
    """ 
    Load team ID and delay from settings.txt or supply defaults
    """
    
    lines = ""
    team = ""
    team_id = ""
    settings_file = '{0}/settings.txt'.format(main_dir)
    if os.path.exists(settings_file):
        # get settings from file
        f = open(settings_file, 'r')
        lines = f.readlines()
    

    # find team_id
    try:
        team_id = lines[1].strip('\n')
    except IndexError:
        team_id = ""
    if team_id == "":
        team = "Hurricanes"

        # query the api to get the ID
        team_id = nhl.get_team_id(team)

    # find delay
    try:
        delay = lines[2].strip('\n')
    except IndexError:
        delay = ""
    if delay is "":
        delay = 0.0
    
    return (team_id, delay)


if __name__ == "__main__":

    old_score = 0
    new_score = 0
    gameday = False
    season = False
    home_score = 0
    away_score = 0 
    home_team = ""
    away_team = ""
    live_stats_link = ""
    x = 0
    y = 0
    home_score_color = ""
    away_score_color = ""
 
    teams = {1 : "NJD", 2 : "NYI", 3 : "NYR", 4 : "PHI", 5 : "PIT", 6 : "BOS", 7 : "BUF", 8 : "MTL", 9 : "OTT", 10 : "TOR", 12 : "CAR", 13 : "FLA", 14 : "TBL", 15 : "WSH", 16 : "CHI", 17 : "DET", 18 : "NSH", 19 : "STL", 20 : "CGY", 21 : "COL", 22 : "EDM", 23 : "VAN", 24 : "ANA", 25 : "DAL", 26 : "LAK", 28 : "SJS", 29 : "CBJ", 30 : "MIN", 52 : "WPG", 53 : "ARI", 54 : "VGK"}
    team_id, delay = setup_nhl()

    try:

        while (True):

            time.sleep(1)
            
            # check if in season
            season = nhl.check_season()
            if season:

                # check game
                gameday = nhl.check_if_game(team_id)

                if gameday:
                    
                    # check end of game
                    game_end = nhl.check_game_end(team_id)
                    
                    if not game_end:
            
                        # Check CAR score online and save score
                        new_score = nhl.fetch_score(team_id)

                        # new function fetch_game(team_id)
                        # returns home_score, home_team, away_score, away_team
                        home_score, home_team, away_score, away_team, live_stats_link = nhl.fetch_game(team_id)
                        #print("Home team: {0} Home score: {1} Away team: {2} Away score: {3}".format( teams[home_team], home_score, teams[away_team], away_score)) 

                        # get stats from the game
                        current_period, home_sog, away_sog, home_powerplay, away_powerplay, time_remaining = nhl.fetch_live_stats(live_stats_link) 

                        # If score change...
                        if new_score != old_score:
                            old_score = new_score

                        ret = client1.publish("canes_data/is_game", "True") 
                        ret = client1.publish("canes_data/current_period", current_period)
                        ret = client1.publish("canes_data/home_sog", home_sog)
                        ret = client1.publish("canes_data/away_sog", away_sog)
                        ret = client1.publish("canes_data/home_powerplay", home_powerplay)
                        ret = client1.publish("canes_data/away_powerplay", away_powerplay)
                        ret = client1.publish("canes_data/time_remaining", time_remaining)
                        ret = client1.publish("canes_data/canes_score", new_score)
                        ret = client1.publish("canes_data/home_score", home_score)
                        ret = client1.publish("canes_data/home_team", home_team)
                        ret = client1.publish("canes_data/away_score", away_score)
                        ret = client1.publish("canes_data/away_team", away_team)

                    else:
                        print("Game Over!")
                        old_score = 0 # Reset for new game
                        ret = client1.publish("canes_data/is_game", "False")
                        sleep("day")  # sleep till tomorrow
                else:
                    print("No Game Today!")
                    ret = client1.publish("canes_data/is_game", "False")
                    sleep("day")  # sleep till tomorrow
            else:
                print("OFF SEASON!")
                ret = client1.publish("canes_data/is_game", "False")
                sleep("season")  # sleep till next season

    except KeyboardInterrupt:
        print("\nCtrl-C pressed")
        client1.loop_stop()
        client1.disconnect()

client1.loop_stop()
client1.disconnect()

