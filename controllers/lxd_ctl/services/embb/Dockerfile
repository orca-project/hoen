FROM python:3.7
ADD video_server.py /
ADD video.mp4 /
EXPOSE 5000/tcp
EXPOSE 5000/udp
RUN pip3 install flask==1.1.1
CMD ["python3", "./video_server.py"]
