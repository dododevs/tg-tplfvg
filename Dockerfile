FROM python:3.12
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r tplfvg_rt_python_api/requirements.txt
CMD ["python", "bot.py"]