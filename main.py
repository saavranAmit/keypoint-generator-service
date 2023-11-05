# Install Python
# Install required modules as follows using pip
# --- Flask
# --- flask-SQLAlchemy = for creating ORM
# --- SpeechRecognition = For recognition of audio from and convert to transcripted text
# --- openai  = For Feching key points fro the transcripted text
# --- logging = For displaying exception, info or warning etc. to developer
# --- spacy = For displaying key points in proper way





from flask import Flask, request, jsonify              #import flask request jsonify from flask
from flask_sqlalchemy import SQLAlchemy                #import SQLAlchemy from flask_sqlalchemy module
from datetime import datetime                          #imtetimeport da
import speech_recognition as sr                        #import speech_recognition
import openai                                          #import openai
import spacy                                           #import spacy
from sqlalchemy.orm.exc import NoResultFound           #import NoResultFound for notifying error
import logging                                         #import logging


nlp = spacy.load("en_core_web_sm")                       #configure spacy

app = Flask(__name__)                                     #object of flask module
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"         #database url (Using sqlite)
db = SQLAlchemy(app)                                                     #creating object of sqlalchemy
openai.api_key = "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"    #openai api key which allow to call it's api

app.app_context().push()                                                #creating table 

class Recording(db.Model):                                            #ORM for Recording table
    id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.Text)                  #Column to store transcribe data
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)   #store date and tie of posting data

# Go to terminal, write python or python3 and click enter button
# write from main import db and click enter button
# write db,create_all() and click enter button
# write exit() and click enter button 
# Your sqlite database will be created


@app.route("/addfile/new", methods=['POST'])              #End point for uploading audio file
def new_post():
    file = request.files.get('file')                      #audio file is saved to file variable

    if not file:                                        #Execute if file not exist
        logging.exception("Audio is required")
        return jsonify({'error': 'Audio is required'}), 400        #error if file not exist

    if file.filename == "":                         #Execute if file variable is empty sting
        logging.exception("Audio is required")
        return jsonify({'error': 'Audio is required'}), 400

    try:                                               #error handling if any error occure except wille execute
        recognizer = sr.Recognizer()                   #object for speechRecognition mpdule
        with sr.AudioFile(file) as source:
            recognizer.adjust_for_ambient_noise(source)   # it resist noice 
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)         #convert audio to text

        post = Recording(transcription=text)           #calling Recording class for posting data
        db.session.add(post)                           #adding post to db
        db.session.commit()                            #commit
        return jsonify({"text": post.transcription, "id": post.id})      #jsonify value return
    except sr.UnknownValueError:                  #error if audio could not understand
        logging.exception("Speech recognition could not understand the audio")   #exception loggging
        return jsonify({'error': 'Speech recognition could not understand the audio'}), 400
    except sr.RequestError:
        logging.exception("Could not request results from Google Web Speech API")
        return jsonify({'error': 'Could not request results from Google Web Speech API'}), 500
    except Exception as e:
        logging.exception("An error occurred during audio processing")
        return jsonify({'error': 'An error occurred during audio processing'}), 500


@app.route("/transcription")              #End point for getting transcription data from table
def getPosts():
    try:
        posts = Recording.query.order_by(Recording.date_posted.desc()).first()    #getting table row 
        if not posts:                               #execute if row does not exist in table
            return jsonify({'error': 'No posts found'}), 404

        array = []
        text = posts.transcription            #Fetch the transcribe data from table
        response = openai.Completion.create(model="text-curie-001",prompt=f'Correct paragraph with proper grammar and punctuation "{text}".',max_tokens=1500)    #calling openai to correct grammar of trancribe data
        translation = response['choices'][0]['text']          #assign correct grammatical transcribe data
        array.append({'text': translation, 'id': posts.id})    #append data to array to return
        return jsonify(array)

    except NoResultFound:        #execute if no result found
        logging.exception("No posts found")
        return jsonify({'error': 'No posts found'}), 404

    except openai.error.OpenAIError as e:     #execute if openai have some issues regarding coreecting grammar
        logging.exception("OpenAI API error")
        return jsonify({'error': 'OpenAI API error'}), 500

    except Exception as e:
        logging.exception("An error occurred")
        return jsonify({'error': 'An error occurred'}), 500


@app.route("/createKeys/<string:text>")   #Endpoint for creating key points from transcribe data
def createKeys(text):
    try:
        arr = []
        response = openai.Completion.create(model="text-curie-001",prompt=f'Generate the summary from given paragraph in same language as paragraph with correct grammar and meaning "{text}" ',max_tokens=1500)   #calling openai to fetch or describe key points from trancribe data
        translation = response['choices'][0]['text']   #key points assign to variable
        doc = nlp(translation)         #key points assign for converting into array

        array = []
        for sentence in doc.sents:      #looping through key point string 
            string = str(sentence)
            array.append(string)      #append one key point at a time

        arr.append({'text': array})
        return jsonify(arr)

    except openai.error.OpenAIError as e:         #execute if openai gives any error
        return jsonify({'error': 'OpenAI API error',}), 500

    except Exception as e:               #execute if exception error occure
        return jsonify({'error': 'An error occurred'}), 500




if __name__ == '__main__':
    app.run(debug=True)