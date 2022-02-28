import json
from urllib import parse, request
import nltk

# Natural Language Tool Kit Setup
from appwrite.exception import AppwriteException

nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from nltk.ccg import chart, lexicon

# Initialize sentiment intensity analyzer
sid = SentimentIntensityAnalyzer()

# Initialize Appwrite SDK
from appwrite.client import Client
from appwrite.services.database import Database

url = "http://api.giphy.com/v1/gifs/search"


def fetch_gif(search_phrase):
    """
    Queries the Giphy search API and returns links to GIFs.
    :type search_phrase: str
    """
    params = parse.urlencode({
        "q": search_phrase,
        "api_key": "7SUIiFi3V22aBZK7oFq22VdBSPzA12a0",
        "limit": "1"
    })

    with request.urlopen("".join((url, "?", params))) as response:
        data = json.loads(response.read())

    return data["data"][0]["images"]["downsized"]["url"]


def analyze_sentiment_by_word(sentence):
    """
    Returns sentiment intensity of each word in the sentence.
    :type sentence: str
    """
    words = sentence.split()
    polarity_scores = [sid.polarity_scores(word)["compound"] for word in words]
    return words, polarity_scores


def pick_max_sentiment_words(sentence):
    """
    Returns word with the strongest sentiment intensity.
    :type sentence: str
    """
    words, polarity_scores = analyze_sentiment_by_word(sentence)
    if max(polarity_scores) < 0.05:
        # If the max polarity is < 0.01, the chat message is neutral, we can just return the entire message
        return sentence
    return words[polarity_scores.index(max(polarity_scores, key=abs))]


def main(req, res):
    client = Client()
    database = Database(client)

    if not req.env.get('APPWRITE_FUNCTION_ENDPOINT') or not req.env.get('APPWRITE_FUNCTION_API_KEY'):
        print('Environment variables are not set. Function cannot use Appwrite SDK.')
    else:
        (
            client
                .set_endpoint('https://bradley-qa2.appwrite.org/v1')
                .set_project(req.env.get('APPWRITE_FUNCTION_PROJECT_ID'))
                .set_key(req.env.get('APPWRITE_FUNCTION_API_KEY'))
                .set_self_signed(True)
        )


    data = json.loads(req.env.get('APPWRITE_FUNCTION_EVENT_DATA'))
    collection_id = data["$collection"]
    document_id = data["$id"]

    """
    The limit for queries is 50 char. If it's a long message, and non of the words have sentimental value,
    the parsed message should be clipped.
    """
    parsed_message = pick_max_sentiment_words(data['message'])[:50]

    document = {
        "user": data['user'],
        "room": data['room'],
        "message": data['message'],
        "meme": fetch_gif(parsed_message)
    }

    ep=req.env.get('APPWRITE_FUNCTION_ENDPOINT')

    print(collection_id, document_id, document, data["$read"], data["$write"])
    try:
        database.update_document(collection_id, document_id, document, data["$read"], data["$write"])
        return res.send('successfully sent message')
    except AppwriteException as e:
        return res.send(f'Unable to update meme for message {e}')


