"""Example of using hangups to send hangouts notifications to the Ergodox"""

import asyncio
import hangups
import serial

from libs.ergodox_infinity_display import ErgodoxInterface

# Path where OAuth refresh token is saved, allowing hangups to remember your
# credentials.
REFRESH_TOKEN_PATH = 'refresh_token.txt'

def main():
    """Main entry point."""
    init_screen()

    # Obtain hangups authentication cookies, prompting for username and
    # password from standard in if necessary.
    cookies = hangups.auth.get_auth_stdin(REFRESH_TOKEN_PATH)
    # Instantiate hangups Client instance.
    client = hangups.Client(cookies)

    # Get the user self info
    loop = asyncio.get_event_loop()
    self_id = loop.run_until_complete(get_self_info(client))

    # Add an observer to the on_connect event to run the send_message coroutine
    # when hangups has finished connecting.
    client.on_state_update.add_observer(lambda event: asyncio.async(get_event(event, client, self_id)))

    # Start an asyncio event loop by running Client.connect. This will not
    # return until Client.disconnect is called, or hangups becomes
    # disconnected.
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.connect())
    except KeyboardInterrupt:
        client.disconnect()

@asyncio.coroutine
def get_self_info(client):
    ''' Get the self info for the currently authenticated user. '''
    client.connect()
    self_info_request = hangups.hangouts_pb2.GetSelfInfoRequest(
            request_header=client.get_request_header(),
    )
    response = yield from client.get_self_info(
        self_info_request
    )
    client.disconnect()
    self_id = response.self_entity.id.chat_id
    return self_id

@asyncio.coroutine
def get_event(event, client, self_id):
    ''' Process a hangups 'on_state_update' message and update the ergodox screen. '''
    try:
        process_event(event, self_id)
    except:
        # Disconnect the hangups Client to make client.connect return.
        yield from client.disconnect()

def init_screen():
    ''' Clears the screen and turns it blue '''
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    ser.close()
    ser.open()
    dox = ErgodoxInterface(ser)
    dox.lcd_hex_color(0x00000C)
    dox.clear()
    ser.close()

def process_event(event, self_id):
    ''' Process a hangups event as nevecessary. '''
    # Open the serial connection to the ergodox
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
    ser.close()
    ser.open()
    dox = ErgodoxInterface(ser)

    # Determine notification type
    notification_type = event.WhichOneof('state_update')
    print("Recieved notification of type {}".format(notification_type))

    if notification_type == 'event_notification':
        # This is our message type
        if event.HasField('conversation'):
            # When we recieve a message
            if event.event_notification.event.sender_id.chat_id != self_id:
                sender = "Unknown"
                for part in event.conversation.participant_data:
                    if part.id.chat_id != self_id:
                        sender = part.fallback_name
                        break
                print("Message with {}() with message id {}".format(sender,
                    event.event_notification.event.sender_id.chat_id,
                     event.conversation.conversation_id.id))
                print("Content: {}".format(event.event_notification.event.chat_message.message_content.segment[0].text))
                # Clear the screen and write the sender name to the top left
                dox.clear()
                dox.lcd.format_string(sender, 0, 24)
                # Color foosball messages a different color
                if 'foos' in event.event_notification.event.chat_message.message_content.segment[0].text:
                    dox.lcd.format_string('FOOSBALL REQUEST!!!', 0, 16)
                    dox.lcd_hex_color(0x0C0C00)
                else:
                    dox.lcd_hex_color(0x0C0000)
                dox.send()
            # When we send a message
            else:
                init_screen()
                print("Message successfully sent.")
    # Message read notification
    elif notification_type == 'watermark_notification':
        # Currently only care about messages we read
        if event.watermark_notification.sender_id.chat_id == self_id:
            print("Conversation {} was read by you".format(event.watermark_notification.conversation_id.id))
            init_screen()

    # Close our serial connection
    ser.close()

class ChatEvent(object):
    def __init__(self, event_type, chat_id):
        self.event_type = event_type
        self.chat_id = chat_id

if __name__ == '__main__':
    main()
