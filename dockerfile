FROM python:3.10.11-slim

WORKDIR /src

COPY requirements.txt /src/

#pip caches downloaded packages in a cache directory (usually ~/.cache/pip) inside the container while installing.
#This cache can add tens or even hundreds of MB to your Docker image, even though you don’t need it after the installation is done.
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install-deps \
    && playwright install firefox

RUN python -c "from faster_whisper import WhisperModel; WhisperModel('distil-small.en')"

#What rm -rf /var/lib/apt/lists/* does:
#This command removes the package lists that apt-get update downloads. 
#When you run apt-get update, it downloads metadata about available packages and stores it in /var/lib/apt/lists/. 
#After installing your packages, you don't need this metadata anymore, 
#so removing it helps reduce your Docker image size. 
#This is a common Docker best practice for keeping images lean.

RUN apt-get update && apt-get install -y xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

COPY /src /src/ 

RUN mkdir ../logs

CMD ["sh", "-c", "xvfb-run -a python -u wiz.py"]

