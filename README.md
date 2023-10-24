# Lab resources

Reusable lab resources live here.

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
task release minor # or major, or patch

# Push it!  (Subject to branch policies)
git push --atomic origin $(git branch --show-current) --follow-tags
```
