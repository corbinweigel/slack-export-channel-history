import os
import json
import time
import threading
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Set the access token for your Slack workspace
slack_client = WebClient(token='slack-token-here')

threads = []

def get_conversation_history(channel_id, conversation_history, cursor=None, page=1, rate_limit_retries=0):
    conversation_history_endpoint = 'conversations.history'
    params = {
        'channel': channel_id,
        'cursor': cursor,
        'limit': 100
    }
    response = slack_client.conversations_history(**params)
    if not response['ok']:
        if response['error'] == 'ratelimited':
            if rate_limit_retries == 6:
                print("Maximum retries hit for rate limiting. Exiting.")
                return
            print("Rate limited, retrying in 30 seconds...")
            time.sleep(30)
            rate_limit_retries += 1
            get_conversation_history(channel_id, conversation_history, cursor, page, rate_limit_retries)
        else:
            print(f"Error occurred: {response['error']}")
            return
    messages = response['messages']
    conversation_history.extend(messages)
    next_cursor = response.get('response_metadata', {}).get('next_cursor')
    if next_cursor:
        thread = threading.Thread(target=get_conversation_history, args=(channel_id, conversation_history, next_cursor, page+1, rate_limit_retries))
        thread.start()
        threads.append(thread)
    print(f"Retrieving conversation history for {channel_id} - page {page} - {len(conversation_history)} messages retrieved", flush=True)

def export_channel_history(channel_id):
    conversation_history = []
    get_conversation_history(channel_id, conversation_history)
    for thread in threads:
        thread.join()
    # Save conversation history to a JSON file
    filename = f"{channel_id}.json"
    with open(filename, 'w') as f:
        json.dump(conversation_history, f)

if __name__ == '__main__':
    channel_id = input("Enter the ID of the channel you want to export: ")
    export_channel_history(channel_id)
    
