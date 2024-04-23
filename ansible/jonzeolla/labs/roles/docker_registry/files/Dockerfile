FROM nginx
RUN groupadd --gid 53150 -r notroot && useradd -r -g notroot -s "/bin/bash" --create-home --uid 53150 notroot
USER notroot
