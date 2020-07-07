FROM python:3.7-slim
ADD control_logic.py /
EXPOSE 9000
RUN pip3 install -Iv pyzmq==17.1.2
CMD python3 ./control_logic.py
