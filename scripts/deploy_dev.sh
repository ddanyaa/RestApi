cd ..
source venv/Scripts/activate
pip freeze > requirements.txt
git add -A
git commit -m "deploy_dev"
git push origin master
ssh dasha@165.22.247.10 'cd project_dev/scripts && sh build.sh'