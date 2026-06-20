from napi.http import HTTP, Reply

@HTTP.GET("/")
def index():
    return Reply.redirect("/static/index.html"), 301

@HTTP.GET("/whitelist")
def whitelist():
    return Reply.redirect("/static/whitelist.html"), 301