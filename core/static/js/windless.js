/*!
 * Chiaki JavaScript Library
 * Copyright (c) 2016 Hieda no Chiaki(i#wind.moe)
 * MIT Licensed
 * @Version Alpha 0.1
 * @Date 09/18/2016 14:49:39 UTC+8
 */

~ function (window, docunment, debug, i) {

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