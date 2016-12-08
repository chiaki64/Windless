/*!
 * Chiaki JavaScript Library
 * Copyright (c) 2016 Hieda no Chiaki(i#wind.moe)
 * MIT Licensed
 * @Version Alpha 0.1
 * @Date 09/18/2016 14:49:39 UTC+8
 */

~ function (window, docunment, debug, i) {

    var _exist = function (value, _default) {
		return value ? value : _default ? _default : false;
	};

    /* Selector */

    i = function (ele) {
        return docunment.querySelector(ele);
    }

    i.getJSON = function (obj) {

        if (window.fetch) {
            tmp = '?';
            for (i in obj.data) {
                tmp += i.toString() + '=' + obj.data[i].toString() + '&';
            }
            if (tmp.charAt(tmp.length - 1) == '&' || tmp.charAt(tmp.length - 1) == '?')
                tmp = tmp.substring(0, tmp.length - 1);
            var url = obj.url + tmp;

            var getData = {
                method: 'GET',
                mode: 'cors',
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }

            fetch(url, getData).then(function (res) {

                if (res.ok) {
                    return res.json().then(function (json) {
                        obj.success(json);
                    });
                } else {
                    console.log("Looks like the response wasn't perfect, got status", res.status);
                }
            }).catch(function (e) {
                console.log("Fetch failed!", e);
            });
        } else {
            
            //传统xhr
        }

    }

    i.img = {
        lazyload: function (high) {

			function getTop(ele) {
				var top = ele.offsetTop;
				while (ele = ele.offsetParent) {
					top += ele.offsetTop;
				}
				return top;
			}

			var imgs = document.body.querySelectorAll('.lazyload'),
				H = window.innerHeight,
				high = _exist(high, 500);

			function lazyload() {
				var S = i('.container').scrollTop;
						[].forEach.call(imgs, function (img) {
					if (!img.getAttribute('data-src')) {
						return;
					}
					if (H + S + high > getTop(img)) {
						img.src = img.getAttribute("data-src");
						img.removeAttribute("data-src");
					}
				});
			}
			i('.container').addEventListener("scroll", lazyload);
		}
    }

    i.img.lazyload();
    window.Chiaki = i;
    typeof ($) === "undefined" ? $ = i: NaN;
    return i;
}(window, document, true);

Title=document.title,
document.addEventListener(
    "visibilitychange",
    function(){
        var e=[
            "╭(′▽`)╯","( ͡° ͜ʖ ͡°)", "(ÒܫÓױ)", "ヽ( ^∀^)ﾉ",
            "(╯°□°)╯︵","(´・ω・`)","(`皿´)",
            "(¬_¬)","(￣▽￣)\"","(〒︿〒)"];
        document.hidden?
            (document.title=e[parseInt(10*Math.random(),10)]+" "+document.title,clearTimeout(2e3)):
            document.title=Title;
    }
);

!function(e){"use strict";var n=function(n,t,o){var l,r=e.document,i=r.createElement("link");if(t)l=t;else{var a=(r.body||r.getElementsByTagName("head")[0]).childNodes;l=a[a.length-1]}var d=r.styleSheets;i.rel="stylesheet",i.href=n,i.media="only x",l.parentNode.insertBefore(i,t?l:l.nextSibling);var f=function(e){for(var n=i.href,t=d.length;t--;)if(d[t].href===n)return e();setTimeout(function(){f(e)})};return i.onloadcssdefined=f,f(function(){i.media=o||"all"}),i};"undefined"!=typeof module?module.exports=n:e.loadCSS=n}("undefined"!=typeof global?global:this);

function theme(){
    if($('#theme').getAttribute('href') == "#"){
        $('#theme').setAttribute('href', '/static/css/windless-night.css');
        window.sessionStorage.setItem('theme', 'stardust');
    }else{
        $('#theme').setAttribute('href', '#');
        window.sessionStorage.setItem('theme', 'lime');
    }
}

document.onkeydown = function(e){
    if (e || (e = window.event), 13 == (e.keyCode || e.which)) {
		if (0 == $("#search-field").value.length)
		    return !1;
		window.location.href = "/?search=" + $("#search-field").value
	}
}
