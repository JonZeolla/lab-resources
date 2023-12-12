# Lab resources

Reusable lab resources live here

## Environmental setup

Ensure you have `docker` and `git` installed locally, and the `docker` daemon is running. Then run the following command to initialize the repository.

```bash
task init
```

## Updating the dependencies

```bash
task update
```

## Creating a release

In order to cut a release, you must additionally have `pipenv` and `python3` installed.

```bash
# Create the release
task release -- minor # or major, or patch

# Push it!  (Subject to branch policies)
git push --atomic origin $(git branch --show-current) --follow-tags
```

## Troubleshooting

If you want to troubleshoot issues using this as a part of a workshop, create a Cloud9 environment, clone the repo that uses this project (i.e.
`policy-as-code`), run `task init` or `git submodule update --init --recursive` from inside that repo folder, and then run the following:

```bash
repo=policy-as-code
role=cloud9
docker run -v ~/environment/${repo}/lab-resources/ansible/jonzeolla/labs/roles/${role}/tasks/main.yml:/root/.ansible/collections/ansible_collections/jonzeolla/labs/roles/${role}/tasks/main.yml --network host -v /:/host jonzeolla/labs:${repo}
```
