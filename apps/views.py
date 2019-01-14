from apps import app, db
from flask import render_template, request, session, redirect, url_for, flash, make_response
from functools import wraps
import requests
from apps.forms import LoginForm, InfoForm, RegistForm, PasswordForm, AlubmCreateForm, AlubmUpload, \
    ArticleCreateForm, AboutMsgForm, AboutDescForm, RandomImgForm

from apps.model import User, Album, Photo, AlbumTag, AlbumLove, Books, \
    BookSection, BookContent, Article, ArticleTag, RandomImg, AboutMsg, AdminTag, ArticleLove

from uuid import uuid4
from datetime import datetime
from bs4 import BeautifulSoup
import random
import re





headers = {
        "Host": "www.biquge5200.cc",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0"
    }



#装饰器登录检查,f:被装饰函数,next指明下一次跳转
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_name' not in session:
            return redirect(url_for('user_login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function




@app.route('/')
def index():
    articles = Article.query.filter(Article.power_id != 2, Article.id < 6).order_by(Article.addtime.desc()).all()
    click = AdminTag.query.filter_by(id=1).first()
    if click == None:
        db.session.add(AdminTag(click_num=0))
        db.session.commit()
        click = AdminTag.query.filter_by(id=1).first()
    click.click_num += 1
    db.session.add(click)
    db.session.commit()
    return render_template('index.html', articles=articles)



@app.route('/user/login/', methods=['GET', 'POST'])
def user_login():

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form['user_name']
        userpassword = (request.form['user_password'])

        user_x = User.query.filter_by(name=username).first()

        if user_x:
            if str(userpassword) == str(user_x.password):
                flash('登录成功', category='ok')
                #写入会话
                session['user_name'] = user_x.name
                session['user_id'] = user_x.id

                return redirect(url_for('index'))
            else:
                flash('密码输入错误', category='err')
                return render_template('user_login.html', form=form)
        else:
            flash('用户不存在', category='err')
            return render_template('user_login.html', form=form)

    return render_template('user_login.html', form=form)



#退出
@app.route('/user/logout/')
def logout():
    #session实质就是一个字典
    session.pop('user_name', None)
    return redirect(url_for('index'))



@app.route('/user/regist/', methods=['GET', 'POST'])
def user_regist():
    form = RegistForm()
    if form.validate_on_submit():

        user_name = request.form['user_name']

        #判断用户是否存在
        user_x = User.query.filter_by(name=user_name).first()
        if user_x:
            flash('用户已经存在', category='err')
        else:
            user = User()
            user.name = user_name
            user.password = request.form['user_password']
            user.email = request.form['user_email']
            user.phone = request.form['user_phone']
            user.sign = request.form['user_sign']
            user.uuid = str(uuid4().hex)


            """写入"""
            db.session.add(user)
            db.session.commit()

            flash('注册成功', category='ok')
            return redirect(url_for('user_login', username=user.name))

    return render_template('user_regist.html', form=form)



@app.route('/user/center/')
@user_login_req
def user_center():
    img_list = []
    imgs = RandomImg.query.all()
    for img in imgs:
        img_list.append(img.img_url)

    img_url = img_list[random.randint(0, 9)]

    return render_template('user_center.html', img_url=img_url)



@app.route('/user/detail/')
@user_login_req
def user_detail():

    user = User.query.filter_by(name=session.get('user_name')).first()

    return render_template('user_detail.html', user=user)



@app.route('/user/password/', methods=['POST', 'GET'])
@user_login_req
def user_password():
    form = PasswordForm()
    if form.validate_on_submit():

        oldpassword = request.form['old_password']
        newpassword = request.form['new_password']
        user = User.query.filter_by(name=session.get('user_name')).first()

        if str(oldpassword) == str(user.password):
            user.password = newpassword
            #自动判断插入或者更新
            db.session.add(user)
            db.session.commit()
            session.pop('user_mame', None)
            flash('修改密码成功, 请重新登录', category='ok')
            return redirect(url_for('user_login', username=user.name))

        else:
            flash('旧密码输入有误', category='err')
            return render_template('user_password.html', form=form)

    return render_template('user_password.html', form=form)



@app.route('/user/info/', methods=['POST', 'GET'])
@user_login_req
def user_info():
    form = InfoForm()
    user = User.query.filter_by(name=session.get('user_name')).first()
    if request.method == 'GET':
        form.user_sign.data = user.sign


    if form.validate_on_submit():

        user.name = request.form['user_name']
        user.email = request.form['user_email']
        user.phone = request.form['user_phone']
        user.sign = form.user_sign.data

        db.session.add(user)
        db.session.commit()
        session['user_name'] = user.name

        return redirect(url_for('user_detail'))

    return render_template('user_info.html', user=user, form=form)


@app.route('/user/del/', methods=['POST', 'GET'])
@user_login_req
def user_del():
    if request.method == 'POST':
        password2 = request.form['new_password2']
        user = User.query.filter_by(name=session.get('user_name')).first()

        if str(password2) == str(user.password):

            # 删除数据
            db.session.delete(user)
            db.session.commit()

            flash('注销成功', category='ok')
            return redirect(url_for('logout'))
        else:
            flash('密码输入有误，请重新输入', category='err')
            return render_template('user_del.html')

    return render_template('user_del.html')




# #创建相册
@app.route('/album/create/', methods=['GET', 'POST'])
@user_login_req
def album_create():

    form = AlubmCreateForm()
    if form.validate_on_submit():
        album_title = form.album_title.data
        album_sign = form.album_sign.data
        see_power = form.see_power.data
        album_tag = form.album_tag.data
        #ps:2018.12.29
        if Album.query.filter_by(title=album_title).first():
            flash('要创建的相册已经存在', category='err')
            return redirect(url_for('album_create'))

        album = Album(title=album_title, album_sign=album_sign,
                      power_id=see_power, tag_id=album_tag,
                      user_id=int(session.get('user_id')))

        db.session.add(album)
        db.session.commit()

        return redirect(url_for('album_upload'))

    return render_template('album_create.html', form=form)




@app.route('/album/list/<int:page>')
def album_list(page):
    albumtags = AlbumTag.query.order_by(AlbumTag.id).all()
    tagid = request.args.get('tag')
    if tagid != None:
        albums = Album.query.filter(Album.power_id != 3, Album.tag_id == int(tagid)).\
            order_by(Album.addtime.desc()).paginate(page=page, per_page=8)
    else:
        albums = Album.query.filter(Album.power_id != 3).order_by(Album.addtime.desc()).paginate(page=page, per_page=8)


    for album in albums.items:
        photo = album.photos[0]

        album.photo_url = photo.ptoto_url

    return render_template('album_list.html', albumtags=albumtags, albums=albums)



@app.route('/album/browse/<int:id>')
def album_browse(id):
    album = Album.query.get(int(id))

    # 点击量
    album.click_num += 1
    db.session.add(album)
    db.session.commit()
    # 查询推荐
    recommd_albums = Album.query.filter(Album.tag_id == album.tag_id, Album.id != album.id).all()

    # 推荐封面
    for item in recommd_albums:
        photo = item.photos[0]

        item.photo_url = photo.ptoto_url

    # 我的收藏
    favor_albums = []
    if 'user_id' in session:
        user = User.query.get(int(session.get('user_id')))
        # 已收藏的相册列表
        for favor in user.album_loves:
            favor_albums.append(favor.album)

        for falbum in favor_albums:
            photo = falbum.photos[0]
            falbum.photo_url = photo.ptoto_url


    temp = render_template('album_browse.html', album=album, recommd_albums=recommd_albums,
                           favor_albums=favor_albums)

    return temp


@app.route('/album/favor/', methods=['GET'])
def album_favor():
    #获取参数
    aid = request.args.get('aid')
    uid = request.args.get('uid')

    #查询判断
    existed = AlbumLove.query.filter_by(user_id=uid, album_id=aid).count()
    album = Album.query.filter_by(id=aid).first()

    if existed >= 1:
        res = {'ok': 0}
    else:

        favor = AlbumLove(user_id=uid, album_id=aid)
        #收藏量
        album.love_num += 1
        db.session.add(album)
        db.session.add(favor)
        db.session.commit()
        res = {'ok': 1}

    import json
    return json.dumps(res)


@app.route('/user/album/favor/')
@user_login_req
def user_album_favor():

    love_albumlist = []
    albumloves = AlbumLove.query.filter_by(user_id=session.get('user_id')).all()
    for albumlove in albumloves:

        album_id = albumlove.album_id
        love_album = Album.query.filter_by(id=album_id).order_by(Album.addtime.desc()).first()
        love_albumlist.append(love_album)

    for love_album in love_albumlist:
        photo = love_album.photos[0]

        love_album.photo_url = photo.ptoto_url


    return render_template('user_album_favor.html', love_albumlist=love_albumlist)





#取消关注
@app.route('/user/album/favor/del/<int:id>')
def user_album_favor_del(id):

    albumlove = AlbumLove.query.filter_by(user_id=session.get('user_id'),
                                           album_id=int(id)).first()
    print(albumlove)
    db.session.delete(albumlove)
    db.session.commit()
    return redirect(url_for('user_album_favor'))





#bookname
@app.route('/book/list/')
def book_list():
    book = Books.query.all()
    if book == []:
        url = 'https://www.biquge5200.cc/xuanhuanxiaoshuo/'
        response = requests.get(url, headers=headers)

        response.encoding = 'gbk'
        after_bs = BeautifulSoup(response.text, 'lxml')

        new_updata = after_bs.find_all('div', class_='l')  # div class=l标签 包裹的内容
        after_new_updata = BeautifulSoup(str(new_updata), 'lxml')

        span2 = after_new_updata.find_all('span', class_='s2')  # 继续筛选书籍
        span5 = after_new_updata.find_all('span', class_='s5')  # 继续筛选作者

        writer_list = []  # 作者list
        for sp5 in span5:
            writer_list.append(sp5.text)

        after_span2 = BeautifulSoup(str(span2), 'lxml')

        a_list = after_span2.find_all('a')
        for a in a_list:
            book_name = a.text  # ----------------小说名
            book_x = Books.query.filter_by(book_name=book_name).first()

            if book_x is None:
                book_url = a.get('href')  # ------------------小说url
                try:
                    writer = writer_list.pop(0)  # -----------------作者
                    book = Books(book_name=book_name, book_writer=writer, book_url=book_url)
                    db.session.add(book)
                    db.session.commit()

                except:
                    pass

    books = Books.query.all()
    return render_template('book_list.html', books=books)

#章节
@app.route('/book/browse/<int:page>')
def book_browse(page):
    page = int(page)
    id = request.args.get('id')
    book = Books.query.get(int(id))

    if book.book_desc == None:
        url = book.book_url
        response = requests.get(url, headers=headers)
        response.encoding = 'gbk'

        after_bs = BeautifulSoup(response.text, 'lxml')

        div_fmimg = after_bs.find('div', id="fmimg")
        img_list = div_fmimg('img')
        for a in img_list:
            img_url = a.get('src')  # ------------图片url
            book.book_img = img_url

        div_intro = after_bs.find('div', id="intro")
        book_desc = div_intro.text  # -----------------------小说简介
        book.book_desc = book_desc
        # ps:2019.1.4  updata book's table
        db.session.add(book)
        db.session.commit()

        """章节部分"""

        dl = after_bs.find_all('dl')
        after_new_updata = BeautifulSoup(str(dl), 'lxml')
        dd_list = after_new_updata.find_all('dd')

        after_dd = BeautifulSoup(str(dd_list), 'lxml')
        a_list = after_dd.find_all('a')

        num = len(a_list) - 9
        for i in range(num):
            section_url = a_list[9 + i].get('href')  # ---------------小说章节url
            section_title = a_list[9 + i].text  # --------------------小说章节标题

            sections = BookSection(section_url=section_url, section_title=section_title, books_id=int(id))
            db.session.add(sections)
            db.session.commit()

    booksections= BookSection.query.filter_by(books_id=int(id)).paginate(page=page, per_page=8)
    count = BookSection.query.filter_by(books_id=int(id)).count()

    if (count/8) > int(count/8):
        count_page = int(count/8) + 1
    else:
        count_page = int(count/8)


    return render_template('book_browse.html', book=book, booksections=booksections, page=page, count_page=count_page)

#正文
@app.route('/book/content/<int:id>')
def book_content(id):
    bookcontent = BookContent.query.filter_by(book_section_id=int(id)).first()
    if bookcontent is None:
        bsc = BookSection.query.get(int(id))
        url = bsc.section_url
        response = requests.get(url, headers=headers)
        response.encoding = 'gbk'
        after_bs = BeautifulSoup(response.text, 'lxml')

        div_content = after_bs.find('div', id="content")  # -------------------小说正文

        content_p = BeautifulSoup(str(div_content), 'lxml')
        content = content_p.text

        contents = BookContent(content=content, book_section_id=int(id))
        db.session.add(contents)
        db.session.commit()

    bookcontent = BookContent.query.filter_by(book_section_id=int(id)).first()
    return render_template('book_content.html', bookcontent=bookcontent, id=id)





@app.route('/article/create/', methods=['GET', 'POST'])
@user_login_req
def article_create():

    form = ArticleCreateForm()
    if form.validate_on_submit():
        article_title = form.article_title.data
        article_img_url = form.article_img_url.data
        article_desc = form.article_desc.data
        see_power = form.see_power.data
        article_tag = form.article_tag.data
        article_text = form.article_text.data

        user_id = int(session.get('user_id'))

        if Article.query.filter_by(article_title=article_title).first():
            flash('要创建的文章标题已经存在', category='err')
            return redirect(url_for('article_create'))

        article = Article(article_title=article_title,
                          article_img_url=article_img_url,
                          article_writer=str(session.get('user_name')),
                          article_desc=article_desc,
                          power_id=see_power,
                          articletag_id=article_tag,
                          article_text=article_text,
                          user_id=user_id)

        db.session.add(article)
        db.session.commit()
        showart = Article.query.filter_by(article_title=article_title).first()
        flash('创建成功', category='ok')
        return render_template('article_create.html', form=form, showart=showart)

    return render_template('article_create.html', form=form)


@app.route('/article/list/<int:page>')
def article_list(page):
    tagid = request.args.get('tag')

    if tagid != None:
        articles = Article.query.filter(Article.power_id != 2, Article.articletag_id == int(tagid)).\
            order_by(Article.addtime.desc()).paginate(page=page, per_page=5)
    else:
        articles = Article.query.filter(Article.power_id != 2).order_by(Article.addtime.desc()).\
                                            paginate(page=page, per_page=5)



    articletags = ArticleTag.query.order_by(ArticleTag.id).all()
    return render_template('article_list.html', articles=articles, articletags=articletags)


@app.route('/article/content/<int:id>')
def article_content(id):

    article = Article.query.filter_by(id=int(id)).first()
    user = User.query.filter_by(id=article.user_id).first()
    article.click_num += 1
    db.session.add(user)
    db.session.commit()
    return render_template('article_content.html', article=article, user=user)




@app.route('/about/me/<int:page>', methods=['GET', 'POST'])
def about_me(page):
    form = AboutMsgForm()
    if form.validate_on_submit():
        user_name = session.get('user_name')
        if user_name:
            about_msg = form.about_msg.data
            aboutmsg = AboutMsg(content=about_msg, user_name=user_name)
            db.session.add(aboutmsg)
            db.session.commit()
        else:
            flash('请先登录', category='err')
            return redirect(url_for('about_me', page=1))

    article_num = Article.query.count()
    album_num = Album.query.count()
    num = AdminTag.query.filter_by(id=1).first()

    if num == None:
        db.session.add(AdminTag(click_num=0))
        db.session.commit()
        num = AdminTag.query.filter_by(id=1).first()
    aboutmsgs = AboutMsg.query.order_by(AboutMsg.addtime.desc()).paginate(page=page, per_page=5)


    return render_template('about_me.html', article_num=article_num, album_num=album_num,
                           num=num, form=form, aboutmsgs=aboutmsgs)




@app.route('/about/del/msg/<int:id>')
def about_del_msg(id):
    about_msg = AboutMsg.query.filter_by(id=int(id)).first()
    db.session.delete(about_msg)
    db.session.commit()
    flash('删除成功', category='ok')
    return redirect(url_for('about_me', page=1))




#管理员
@app.route('/admin/user/info/')
@user_login_req
def admin_user_info():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':
            users = User.query.all()
            return render_template('admin_user_info.html', users=users)
        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))



@app.route('/admin/user/article/')
@user_login_req
def admin_user_article():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':
            articles = Article.query.order_by(Article.addtime.desc()).all()
            return render_template('admin_user_article.html', articles=articles)
        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))




#上传图片
@app.route('/album/upload/', methods=['GET', 'POST'])
@user_login_req
def album_upload():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':

            form = AlubmUpload()

            albums = Album.query.filter_by(user_id=session.get('user_id')).all()
            form.album_title.choices = [(album.id, album.title) for album in albums]

            if form.validate_on_submit():

                album = Album.query.filter_by(id=form.album_title.data).first()
                album_photo = request.form['album_photo']

                re_obj = re.compile("[a-zA-z]+://[^\s]*")
                album_photourls = (re_obj.findall(album_photo))


                success = 0
                fail = 0
                start = datetime.now().strftime('%S')
                for ptoto_url in album_photourls:
                    try:
                        photo = Photo(ptoto_url=ptoto_url, album_id=album.id)
                        db.session.add(photo)
                        db.session.commit()
                        success += 1
                    except:
                        fail += 1

                album.photo_num += success
                db.session.add(album)
                db.session.commit()

                end = datetime.now().strftime('%S')
                flash('目前相册共有%s张,本次上传成功%s张,失败%s张,共用时%s秒'%
                      (album.photo_num, success, fail, (float(end) - float(start))), category='ok')
                return render_template('album_upload.html', form=form, album_photourls=album_photourls)

            return render_template('album_upload.html', form=form)

        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))



@app.route('/user/album/mine/')
@user_login_req
def user_album_mine():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':

            albums = Album.query.filter_by(user_id=session.get('user_id')).order_by(Album.addtime.desc()).all()

            for album in albums:
                photo = album.photos[0]
                album.photo_url = photo.ptoto_url

            return render_template('user_album_mine.html', albums=albums)
        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))



#删除发布的相册
@app.route('/user/album/del/<int:id>')
def user_album_del(id):

    album = Album.query.filter_by(id=int(id)).first()
    album_loves = album.album_loves
    photos = album.photos

    for photo in photos:
        db.session.delete(photo)
        db.session.commit()
    for album_love in album_loves:
        db.session.delete(album_love)
        db.session.commit()
    db.session.delete(album)
    db.session.commit()

    return redirect(url_for('user_album_mine'))


#删除发布的文章
@app.route('/user/article/del/<int:id>')
def user_article_del(id):

    article = Article.query.filter_by(id=int(id)).first()

    db.session.delete(article)
    db.session.commit()

    return redirect(url_for('admin_user_article'))




#关注文章
@app.route('/article/favor/', methods=['GET'])
def article_favor():
    #获取参数
    aid = request.args.get('aid')
    uid = request.args.get('uid')

    #查询判断
    existed = ArticleLove.query.filter_by(user_id=uid, article_id=aid).count()
    article = Article.query.filter_by(id=aid).first()

    if existed >= 1:
        res = {'ok': 0}
    else:

        favor = ArticleLove(user_id=uid, article_id=aid)
        #收藏量
        article.love_num += 1
        db.session.add(article)
        db.session.add(favor)
        db.session.commit()
        res = {'ok': 1}

    import json
    return json.dumps(res)



@app.route('/user/music/')
def user_music():

    return render_template('user_music.html')



@app.errorhandler(404)
def page_not_found(err):
    #在响应头添加信息
    resp = make_response(render_template('404.html'), 404)
    resp.headers['X-SS'] = 'hello'
    return resp


#关注文章
@app.route('/user/article/favor/')
@user_login_req
def user_article_favor():

    love_articlelist = []
    articleloves = ArticleLove.query.filter_by(user_id=session.get('user_id')).all()
    for articlelove in articleloves:

        article_id = articlelove.article_id
        love_article = Article.query.filter_by(id=article_id).order_by(Article.addtime.desc()).first()
        love_articlelist.append(love_article)

    return render_template('user_article_favor.html', love_articlelist=love_articlelist)





#取消关注
@app.route('/user/article/favor/del/<int:id>')
def user_article_favor_del(id):
    print(id)
    articlelove = ArticleLove.query.filter_by(user_id=session.get('user_id'), article_id=int(id)).first()

    db.session.delete(articlelove)
    db.session.commit()
    return redirect(url_for('user_article_favor'))





@app.route('/admin/about/desc/', methods=['GET', 'POST'])
@user_login_req
def admin_about_desc():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':
            form = AboutDescForm()
            if form.validate_on_submit():
                about_desc = request.form['about_desc']

                admin_tag = AdminTag.query.filter_by(id=1).first()
                admin_tag.desc = about_desc
                db.session.add(admin_tag)
                db.session.commit()
                flash('修改成功', category='ok')

            return render_template('admin_about_desc.html', form=form)

        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))





@app.route('/admin/random/img/', methods=['GET', 'POST'])
@user_login_req
def admin_random_img():
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':
            form = RandomImgForm()
            if form.validate_on_submit():
                random_img = request.form['random_img']

                re_obj = re.compile("[a-zA-z]+://[^\s]*")
                random_imgurls = (re_obj.findall(random_img))
                success = 0
                fail = 0

                start = datetime.now().strftime('%S')
                for img_url in random_imgurls:
                    try:
                        random_img = RandomImg(img_url=img_url)
                        db.session.add(random_img)
                        db.session.commit()
                        success += 1
                    except:
                        fail += 1

                img_num = RandomImg.query.count()

                end = datetime.now().strftime('%S')
                flash('目前随机图片共有%s张,本次上传成功%s张,失败%s张,共用时%s秒' %
                      (img_num, success, fail, (float(end) - float(start))), category='ok')
            imgurls = RandomImg.query.order_by(RandomImg.id.desc()).all()
            return render_template('admin_random_img.html', form=form, imgurls=imgurls)
        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))




@app.route('/admin/random/img/del/<int:id>')
@user_login_req
def admin_random_img_del(id):
    user_name = session.get('user_name')
    user_id = session['user_id']
    admintag = AdminTag.query.filter_by(id=1).first()
    if admintag:
        if str(user_name) == str(admintag.name) and str(user_id) == '1':

            random_img = RandomImg.query.filter_by(id=int(id)).first()
            db.session.delete(random_img)
            db.session.commit()
            flash('删除成功', category='ok')
            return redirect(url_for('admin_random_img'))
        else:
            flash('you are not admin!', category='ok')
            return redirect(url_for('index'))
    else:
        flash('you are not admin!', category='ok')
        return redirect(url_for('index'))