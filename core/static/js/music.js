~ function () {
    var musicList = [
    {
        'Artist': 'Suara',
        'Album': '「Pure -AQUAPLUS LEGEND OF ACOUSTICS-」',
        'Source': 'https://dn-wind-moe.qbox.me/static/music/Suara - 梦想歌.mp3?ver=1.0',
        'Title': '梦想歌',
        'Duration': '247'
		}, {
        'Artist': 'Suara',
        'Title': '不安定な神様',
        'Album': '「不安定な神様」',
        'Source': 'https://dn-wind-moe.qbox.me/static/music/Suara - 不安定な神様.mp3',
        'Duration': '244'
		}
	];

    var se = sessionStorage;
    var audio = $('#audio');

    if(se.getItem('mode')){
        var musicMode = se.getItem('mode')
    }else {
        var musicMode = 'list'
    }

    function change() {
        if(se.getItem('index') && se.getItem('current')) {
            audio.currentTime = parseFloat(se.getItem('current'));
        }
    }

    var bufferTimer = null;
    var volumeTimer = null;


    $('.play').onclick = function () {
        toPlay('play');
    }
    $('.pause').onclick = function () {
        toPlay('pause');
    }
    $('.prev').onclick = function () {
        toPlay('prev');
    }
    $('.next').onclick = function () {
        toPlay('next');
    }
    $('.progress_bar').onclick = function (ev) {
            adjustPorgress(this, ev);
        }

    $('.volume').onmouseover = $('.volume_wrap').onmouseover = function () {
        clearTimeout(volumeTimer);
        removeClass($('.volume_wrap'), 'hidden')
    };
    $('.volume').onmouseout = $('.volume_wrap').onmouseout = function () {
        volumeTimer = setTimeout(function () {
            addClass($('.volume_wrap'), 'hidden');
        }, 300);
    };
    $('.volume_bar').onclick = function (ev) {
        adjustVolume(this, ev);
    };

    $('.volume').onclick = function () {
        if (audio.muted == false) {
            this.style.color = '#A1A1A1';
            audio.muted = true;
            se.setItem('muted', 1);
        } else if (audio.muted == true) {
            this.style.color = '#8BC34A';
            audio.muted = false;
            se.setItem('muted', 0);
        };
    };

    $('.shuffle').onclick = function () {
        if(musicMode=='list'){
            changeMusicMode(this, 'shuffle')
        }else{
            changeMusicMode(this, 'list')
        }
    };

    audio.addEventListener('canplay', bufferBar, false);

    function initPlayer(index) {
        console.log(index)
        audio.setAttribute('src', musicList[index].Source);
        $('.song').innerHTML = musicList[index].Title;
        $('.album').innerHTML = musicList[index].Album;
        $('.progress').style.width = 0 + 'px';
        audio.removeEventListener('canplay', bufferBar, false);
        clearInterval(bufferTimer);
        $('.buffer').style.width = 0 + 'px';
    }

    function toPlay(action) {
        if (action == 'play') {
            audio.play();
            removeClass($('.pause'), 'hidden');
            addClass($('.play'), 'hidden');
            se.setItem('pause', 0)
        } else if (action == 'pause') {
            audio.pause();
            removeClass($('.play'), 'hidden');
            addClass($('.pause'), 'hidden');
            se.setItem('pause', 1)
        } else if (action == 'prev') {
            playMusicMode(action);
        } else if (action == 'next') {
            playMusicMode(action);
        }
    }

    audio.addEventListener('ended', function () {
        playMusicMode('ended');
    }, false);


    function playMusicMode(action) {
        var MusicNum = musicList.length;
        var index = musicIndex;

        //list loop
        if (musicMode == 'list') {
            if (action == 'prev') {
                if (index == 1) {
                    index = MusicNum; //第一首歌则返回最后一首
                } else {
                    index -= 1;
                }
            } else if (action == 'next' || action == 'ended') {
                if (index == MusicNum) {
                    index = 1;
                } else {
                    index += 1;
                }
            }
        }

        if (musicMode == 'shuffle') {
            var randomIndex = parseInt(MusicNum * Math.random());
            index = randomIndex + 1;
        }

        musicIndex = index;
        playIndex(index - 1);
    }

    function playIndex(index) {
        index = parseInt(index);
        initPlayer(index);
        audio.load();
        audio.addEventListener('canplay', bufferBar, false);
        toPlay('play');
        se.setItem('index', index + 1)
    }

    function changeMusicMode(dom, mode) {
        musicMode = mode;
        if(musicMode=='shuffle'){
            dom.style.color = '#8BC34A';
        }else{
            dom.style.color = '#A1A1A1';
        }
        se.setItem('mode', mode);
    }

    audio.addEventListener('timeupdate', function () {
        if (!isNaN(audio.duration)) {
			sessionStorage.setItem('current',audio.currentTime);

            var curMin = parseInt(audio.currentTime / 60);
            var curSec = parseInt(audio.currentTime % 60);
            if(curSec < 10){curSec = '0'+curSec;}
            var totalMin = parseInt(audio.duration / 60);
            var totalSec = parseInt(audio.duration % 60);
            if(totalSec < 10){totalSec = '0'+totalSec;}

            $('.time').innerHTML = curMin + ":" + curSec + "/" + totalMin + ":" + totalSec;

            var progressValue = audio.currentTime / audio.duration * 324;
            $('.progress').style.width = parseInt(progressValue) + 'px';
        };
    }, false);

    function bufferBar() {
        bufferTimer = setInterval(function () {
            var bufferIndex = audio.buffered.length;
            if (bufferIndex > 0 && audio.buffered != undefined) {
                var bufferValue = audio.buffered.end(bufferIndex - 1) / audio.duration * 324;
                $('.buffer').style.width = parseInt(bufferValue) + 'px';

                if (Math.abs(audio.duration - audio.buffered.end(bufferIndex - 1)) < 1) {
                    $('.buffer').style.width = 324 + 'px';
                    clearInterval(bufferTimer);
                };
            };
        }, 1000);
    }

    function adjustPorgress(dom, ev) {
        var event = window.event || ev;
        var progressX = event.clientX - dom.getBoundingClientRect().left;
        audio.currentTime = parseInt(progressX / 324 * audio.duration);
        audio.removeEventListener('canplay', bufferBar, false);
    }

    function adjustVolume(dom, ev) {
        var event = window.event || ev;
        var volumeY = dom.getBoundingClientRect().bottom - event.clientY;
        audio.volume = (volumeY / 80).toFixed(2);
        $('.volume_now').style.height = volumeY + 'px';
        se.setItem('volume', (volumeY / 80).toFixed(2));
    };

	function adjustplay(time) {
		audio.currentTime = parseFloat(time);
		audio.removeEventListener('canplay', bufferBar, false);
	}

    function hasClass(dom, className) {
        var classNum = dom.className.split(" "),
            hasClass;
        for (var i = 0; i < classNum.length; i++) {
            if (classNum[i] == className) {
                hasClass = true;
                break;
            } else {
                hasClass = false;
            };
        };
        return hasClass;
    }

    function addClass(dom, className) {
        if (!hasClass(dom, className)) {
            dom.className += " " + className;
        };
    }

    function removeClass(dom, className) {
        if (hasClass(dom, className)) {
            var classNum = dom.className.split(" ");
            for (var i = 0; i < classNum.length; i++) {
                if (classNum[i] == className) {
                    classNum.splice(i, 1);
                    dom.className = classNum.join(" ");
                    break;
                };
            };
        };
    }

    function replaceClass(dom, className, replaceClass) {
        if (hasClass(dom, className)) {
            var classNum = dom.className.split(" ");
            for (var i = 0; i < classNum.length; i++) {
                if (classNum[i] == className) {
                    classNum.splice(i, 1, replaceClass);
                    dom.className = className.join(" ");
                    break;
                };
            };
        };
    }

    $('.dialog-close-button').onclick = function(){
        addClass($('#music'), 'hidden')
    }

    $('#mbtn').onclick = function(){
        if(hasClass($('#music'), 'hidden')){
            removeClass($('#music'), 'hidden')
        }else{
            addClass($('#music'), 'hidden')
        }
    }
    se.setItem('mode', 'list')
	if(se.getItem('index')){
        var musicIndex = se.getItem('index')
    }else {
        var musicIndex = 1;
        se.setItem('index', musicIndex)
    }
    initPlayer(musicIndex - 1);

     if (se.getItem('volume')) {
		audio.volume = se.getItem('volume');
		$('.volume_now').style.height = se.getItem('volume') * 80 + "px";
	} else {
		audio.volume = .5
	};

	if(se.getItem('pause') && se.getItem('pause') == 0){
	    setTimeout(function () {
            audio.play();
            change();
        }, 150);
        addClass($('.play'), 'hidden');
        removeClass($('.pause'), 'hidden');
	}

	if (se.getItem("muted") == 1) {
		$(".volume").style.color = '#A1A1A1';
		audio.muted = !0;
	};
}();


var oDiv=$("#music_drap"),
    oTag=$('#music');
fnDrafting(oDiv, oTag);
function fnDrafting(obj, tag){
    obj.onmousedown=function(ev){
        var oEvent=ev||event,
			disX=oEvent.clientX-tag.offsetLeft,
			disY=oEvent.clientY-tag.offsetTop;
        document.onmousemove=function(ev){
            var oEvent=ev||event,
                left=oEvent.clientX-disX,
				top=oEvent.clientY-disY;
            if(left<0){
                left=0;
            }else if(left>document.documentElement.clientWidth-tag.offsetWidth){
                left=document.documentElement.clientWidth-tag.offsetWidth;
            }
            if(top<0){
                top=0;
            }else if(top>document.documentElement.clientHeight-tag.offsetHeight){
                top=document.documentElement.clientHeight-tag.offsetHeight;
            }
            tag.style.left=left+'px';
            tag.style.top=top+'px';
        }
        document.onmouseup=function(){
            document.onmousemove=null;
            document.onmouseup=null;
        }
    }

}
