# canesbroker
NHL data parser and MQTT publisher for Carolina Hurricanes

Reads the JSON data from the NHL API and retrieves game data for the current Carolina Hurricanes game. Score data is published to an MQTT broker so simple clients can subscribe and do something eg. turn on a lamp for a goal light.

You can test simply with the mosquitto MQTT client like so:
mosquitto_sub --id tester --port 1883 -h ec2-18-221-202-45.us-east-2.compute.amazonaws.com  -t canes_data/canes_score -u "goallight" -P "bunchofjerks"

When a game is in progress you will see the score refreshed about once per second. This is done so a client can display a score immediately. Simple stuff like a goal light could get by with only updates during a score change.`
