FROM juniper/pyez 

WORKDIR /app

COPY config_push.py /app/

ENTRYPOINT ["/usr/bin/python3", "/app/config_push.py"]
CMD ["--help"]
