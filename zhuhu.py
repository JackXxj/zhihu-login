'''
# 知乎的模拟登录
#
# cookielib:
# cookielib模块的主要作用是提供可存储cookie的对象，以便于与requests模块配合使用来访问Internet资源。例如可以利用本模块的CookieJar类的对象来捕获cookie并在后续连接请求时重新发送
#
#
'''

import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
import os.path
from bs4 import BeautifulSoup
try:
    from PIL import Image
except:
    pass


# 构造 Request headers
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
headers = {
    'User-Agent': agent,
}

# 使用登录cookie信息
session = requests.session()

session.cookies = cookielib.LWPCookieJar(filename='cookies')      #将获取的cookie保存到cookies文件中
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")


def get_xsrf():
    '''_xsrf 是一个动态变化的参数,所以每次重新登录的时候需要重新获取'''
    index_url = 'https://www.zhihu.com'
    index_page = session.get(index_url, headers=headers)
    html = index_page.text
    pattern = r'name="_xsrf" value="(.*?)"'
    _xsrf = re.findall(pattern, html)
    return _xsrf[0]


# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha\n>")
    return captcha


def isLogin():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=headers, allow_redirects=False)
    if login_code.status_code == 200:
        bs = BeautifulSoup(login_code.text,'lxml')
        name = bs.find_all('span',attrs='name')[0].string
        print(name)     #如果登录之后就会显示登录后的信息
        return name
    else:
        return False


def login(user, password):
    _xsrf = get_xsrf()
    headers["X-Xsrftoken"] = _xsrf
    headers["X-Requested-With"] = "XMLHttpRequest"
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", user):
        print("手机号登录 \n")
        post_url = 'https://www.zhihu.com/login/phone_num'
        postdata = {
            '_xsrf': _xsrf,
            'password': password,
            'phone_num': user
        }
    else:
        if "@" in user:
            print("邮箱登录 \n")
        else:
            print("你的账号输入有问题，请重新登录")
            return 0
        post_url = 'https://www.zhihu.com/login/email'
        postdata = {
            '_xsrf': _xsrf,
            'password': password,
            'email': user
        }
    # 不需要验证码直接登录成功
    login_page = session.post(post_url, data=postdata, headers=headers)
    login_code = login_page.json()
    # print(login_code)
    if login_code['r'] == 1:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        postdata["captcha"] = get_captcha()
        login_page = session.post(post_url, data=postdata, headers=headers)    #如果需要验证码才能登录，需要将验证码放到data中，一起post过去
        login_code = login_page.json()
        print(login_code['msg'])
    # 保存 cookies 到文件，
    # 下次可以使用 cookie 直接登录，不需要输入账号和密码
    session.cookies.save()


if __name__ == '__main__':
    if isLogin():
        print('您已经登录')
    else:
        user = input('请输入你的用户名\n>  ')
        password = input("请输入你的密码\n>  ")
        login(user, password)
