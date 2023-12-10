import os
import re
import sys 
import requests

URLs = ["https://api.github.com/repos/SzachMaty-Company/Frontend/releases/latest"]
IMAGE_DIR = "images/"


def error(text):    
    sys.stderr.write(f'Jestem zniesmaczony twoja osoba. {text}\n')

def getResponse(URL, authToken):
    headers = {
        'Authorization' : f'Bearer {authToken}',
        'X-GitHub-Api-Version': '2022-11-28',
        'Accept': 'application/vnd.github+json'
    }
    resp = requests.get(URL, headers=headers)

    if resp.status_code == 200:
        return resp
    elif resp.status_code == 401:
        error("jestes nie powazny, token jest nie prawidlowy. Powinien wygladac: ghp_***********")

def getUrlAndNameForDockerImageFileFromResponse(resp):
    try:
        asset = resp.json()["assets"][0]
        return asset["url"], asset["name"]
    except:
        error("pan json zgubil pole")

def getImageFromUrl(url, fileName, authToken):
    headers = {
        'Authorization' : f'Bearer {authToken}',
        'X-GitHub-Api-Version': '2022-11-28',
        'Accept': 'application/octet-stream'
    }
    filePath = IMAGE_DIR + fileName

    with requests.get(url, headers=headers, stream=True) as response:
        if response.status_code == 200:
            with open(filePath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return filePath
        else:
            raise Exception(f"Failed to download '{url}'. Status code: {response.status_code}")

def downloadImage(url):
    try:
        resp = getResponse(url, token)
        urlDockerImage, nameDockerImage = getUrlAndNameForDockerImageFileFromResponse(resp)
        return getImageFromUrl(urlDockerImage, nameDockerImage, token)
    except Exception as e:
        error(e)
        return None
    
def findInFileAndReplace(file, name, ver):
    pattern = rf'{name}:\d+(\.\d+)+'
    replacement = f"{name}:{ver}"
    return re.sub(pattern, replacement, file)
    

if __name__ == "__main__":

    token = os.environ.get('SZACHMATY_GIT_TOKEN')
    if token == None:
        error("Nie ustawiles zmiennej srodowiskowej SZACHMATY_GIT_TOKEN.")
        exit(1)

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)


    imagesPaths = []
    try:
        for url in URLs:
            resp = getResponse(url, token)
            urlDockerImage, nameDockerImage = getUrlAndNameForDockerImageFileFromResponse(resp)
            imagesPaths.append(getImageFromUrl(urlDockerImage, nameDockerImage, token))
    except Exception as e:
        error(e)

    images = []
    for imagePath in imagesPaths:
        imageNameJoined = imagePath.split('/')[1][:-4]
        vIndex = imageNameJoined.rfind('v')
        name, ver = imageNameJoined[:vIndex], imageNameJoined[vIndex+1:]
        os.system(f"docker load --input {imagePath}")
        images.append((name, ver))

    resultingDockerCompose = open("docker-compose.yml").read()
    for name, ver in images:
        print(name, ver)
        resultingDockerCompose = findInFileAndReplace(resultingDockerCompose, name, ver)
    print(resultingDockerCompose)

