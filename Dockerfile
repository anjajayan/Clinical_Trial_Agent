FROM python:3.11
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"
WORKDIR /api
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY --chown=user . /api
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]