function toggle(showHideDiv, switchImgTag) {
      var ele = document.getElementById(showHideDiv);
      var imageEle = document.getElementById(switchImgTag);
      if(ele.style.display == "block") {
        ele.style.display = "none";
		    imageEle.innerHTML = '<img src='+ filter_arrow_down + '>';
      } else {
        ele.style.display = "block";
        imageEle.innerHTML = '<img src='+ filter_arrow_up + '>';
      }
    }
