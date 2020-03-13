FROM python:3.7-alpine
ADD video_server.py /
EXPOSE 5000
RUN pip3 install -Iv flask==1.1.1
CMD python3 ./video_server.py
