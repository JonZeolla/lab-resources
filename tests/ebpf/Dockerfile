FROM ghcr.io/astral-sh/uv:0.12.14 AS uv
FROM rockylinux:8
COPY --from=uv /uv /usr/local/bin/uv
RUN dnf install -y sudo && dnf clean all && uv tool install --python 3.12 ansible-core==2.16.19
ENV PATH=/root/.local/bin:$PATH ANSIBLE_COLLECTIONS_PATH=/collections
COPY ansible/jonzeolla/labs /collections/ansible_collections/jonzeolla/labs
COPY tests/ebpf /tests
CMD ["ansible-playbook", "-i", "localhost,", "-c", "local", "/tests/verify.yml"]
