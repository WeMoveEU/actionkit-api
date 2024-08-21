# Upload a actionkit package to Gitlab


1. Build the package: `python setup.py sdist bdist_wheel`
2. Create an API token here: https://gitlab.wemove.eu/-/profile/personal_access_tokens
3. Create `~/.pypirc` with:

   ```
   [distutils]
   index-servers = gitlab

   [gitlab]
   repository = https://gitlab.wemove.eu/api/v4/projects/62/packages/pypi
   username = HOW_YOU_NAMED_TOKEN
   password = $TOKEN
   ```

   (62 is the id of actionkit project)
4. Upload the package: `python3 -m twine upload --verbose --repository gitlab dist/*`
