import sys
from identity_automation import app
from identity_automation.common import constants

for i in range(1, len(sys.argv)):
    if sys.argv[i] == '?':
        print ('Options: --disabled_users, --log_to_screen, --simulate')
    if sys.argv[i] == '--disabled_users':
        constants.execute_moving_past_users = True
        constants.execute_disabling_past_users = True

    if sys.argv[i] == '--log_to_screen':
        constants.logging_log_to_screen = True
    else:
        constants.logging_log_to_screen = False

    if sys.argv[i] == '--simulate':
        constants.execute_changes = False
    else:
        constants.execute_changes = True
app.run()