import requests
import csv 
from bs4 import BeautifulSoup as bs
from datetime import date 
import os 
import logging
from flask import Flask , jsonify
from dotenv import load_dotenv
from github import Github , InputGitTreeElement
import glob

load_dotenv()

# Setup Logger
logging.basicConfig(filename="log.txt" , format="%(asctime)s %(message)s" , filemode = "a")
logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)

# Constants
URL = "https://www.mohfw.gov.in/"
DATAFOLDER = os.path.join(os.curdir , "data")
CSV_HEADERS = ["state/ut" , "cofirmed (indian)" , "confirmed (foreign)" , "cured/discharged" , "death"]
REPO_NAME = "ncov-19-india"
# Functions
def get_scrapped_data(URL):
    try:
        page = requests.get(URL).text
        return bs(page , "html.parser")
    except Exception as e:
        print(e)
        logger.error(f"Got Error While Fetching Source : {str(e)}")
        return False

def print_data():
    try:
        soup = get_scrapped_data(URL)
        for tr in soup.find_all('tr')[1:-1]:
            tds = tr.find_all('td')
            print(f"State/UT: {tds[1].text}, Confirmed (Indian National): {tds[2].text}, Confirmed (Foreign National): {tds[3].text}, Cured/Discharged: {tds[4].text}, Death: {tds[5].text}")
        return True
    except Exception as e:
        print(e)
        logger.error(f"Got Error While Printing Table : {str(e)}")


def write_csv(filename=None):
    try:
        if filename is None:
            filename = str(date.today().isoformat()) + ".csv"

        if not os.path.isdir(DATAFOLDER):
            os.mkdir(DATAFOLDER)

        if not os.path.isfile(DATAFOLDER):
            open(os.path.join(DATAFOLDER , filename) , "w").close()

        with open(os.path.join(DATAFOLDER , filename) , "w") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            soup = get_scrapped_data(URL)
            for tr in soup.find_all("tr")[1:-1]:
                tds = tr.find_all("td")
                writer.writerow([tds[1].text , tds[2].text , tds[3].text , tds[4].text , tds[5].text])
        return True
    except Exception as e:
        print(e)
        logger.error("Got Error While Writing CSV : {}".format(str(e)))
        return False


def push_to_github():
    file_list = glob.glob(os.path.join(DATAFOLDER , "*.csv"))
    TOKEN = os.getenv("GHTOKEN")
    g = Github(TOKEN)
    nrepo = g.get_user().get_repo(REPO_NAME)
    commit_msg = "Auto Update Data"
    master_ref = nrepo.get_git_ref("heads/master")
    master_sha = master_ref.object.sha
    base_tree= nrepo.get_git_tree(master_sha)
    elist = []
    for i , entry in enumerate(file_list):
        with open(entry) as input_file:
            data = input_file.read()
        elem = InputGitTreeElement("data/" + entry[-14:] , '100644' , 'blob' , data)
        elist.append(elem)
    tree = nrepo.create_git_tree(elist)
    parent = nrepo.get_git_commit(master_sha)
    commit = nrepo.create_git_commit(commit_msg , tree , [parent])
    master_ref.edit(commit.sha)
    #print(elist)




if __name__ == "__main__":
    push_to_github()
    #c = write_csv()
    #if c:
    #    logger.info("Completed!")
    #else:
    #    logger.critical("Failed!")

