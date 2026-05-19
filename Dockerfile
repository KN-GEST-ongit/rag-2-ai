FROM python:3.9

WORKDIR /app
COPY "requirements.txt" .

RUN pip install virtualenv
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN python -m pip install pip==21.1.2
RUN pip install --no-cache-dir -r requirements.txt

COPY "/" .

CMD ["python","-u","main.py"]
