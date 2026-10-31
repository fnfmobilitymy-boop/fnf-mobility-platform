FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY source/seo/pricing.py source/seo/catalogue.py source/seo/payment-details.json source/seo/policy.py /app/source/seo/
COPY backend /app/backend
RUN chmod -R a+rX /app
WORKDIR /app/backend
EXPOSE 10000
CMD ["python", "entrypoint.py"]
