import redis
import json


def push_to_logging(message: str, title: str, append: bool = False):
    """Push a message to the Redis chat queue"""
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.publish('logging_messages', json.dumps({"message": message, "title": title, "append": append}))


def stream_chat():
    print('------------------- 1')
    r = redis.Redis(host='localhost', port=6379, db=0)
    pubsub = r.pubsub()
    print('------------------- 2')
    print(pubsub.get_message())
    pubsub.subscribe('logging_messages')
    print('------------------- 3')
    # Initial message
    yield {"message": "Starting thought logging...\n", "title": None, "append": False}

    # Keep listening for messages
    for message in pubsub.listen():
        print("GOT MESSAGE", message)
        if message['type'] == 'message':
            # Decode the message from bytes to string
            print("GOT MESSAGE", message)
            try:
                msg = json.loads(message['data'].decode('utf-8'))
                yield msg
            except Exception as e:
                print("ERROR", e)
                msg = message['data']

