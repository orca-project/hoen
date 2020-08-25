FROM python:3.7
ADD control_logic.py /
EXPOSE 9000/tcp
EXPOSE 9000/udp
RUN pip3 install pyzmq==17.1.2
CMD ["python3", "./control_logic.py"]
