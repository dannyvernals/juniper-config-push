# sudo docker build -t test-script2 .
# note there have been issues here with sudo timelags: I think down to the fact that docker build does further auth using dbus keyring
# The keyring is owned by user not root and dbus has some security checks to prevent this from succeeding, 
# sudo -E (pass env vars) could help, we need DBUS_SESSION_BUS_ADDRESS
# as could seteuid in a wrapper before calling docker
# docker run --rm -it -v ${PWD}:/tmp test-script /tmp/routers /tmp/test_config set

FROM juniper/pyez 

WORKDIR /app

COPY config_push.py /app/

ENTRYPOINT ["/usr/bin/python3", "/app/config_push.py"]
CMD ["--help"]
