#!/usr/bin/env python3
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route("/video", methods=["GET"])
def get_movie():
    return send_from_directory(
                "/root/services/",
                "video.mp4",
                conditional=True,
            )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)